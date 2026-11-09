"""Narrow fixed-cell changes to the preserved A37 QCDT."""
import struct

def properties(dtb):
    if len(dtb)<40:raise ValueError('Short FDT')
    magic,total,structure,strings,reserve,version,last,boot,string_size,struct_size=struct.unpack_from('>10I',dtb)
    if magic!=0xd00dfeed or total>len(dtb) or version!=17:raise ValueError('Unexpected FDT header')
    if strings+string_size>total or structure+struct_size>total:raise ValueError('FDT range outside image')
    cursor=structure; end=structure+struct_size; stack=[]; nodes={}
    while cursor<end:
        token=struct.unpack_from('>I',dtb,cursor)[0];cursor+=4
        if token==1:
            stop=dtb.find(b'\0',cursor,end)
            if stop<0:raise ValueError('Unterminated FDT node')
            stack.append(dtb[cursor:stop].decode('ascii'))
            cursor=(stop+4)&~3
            path='/'+'/'.join(x for x in stack if x)
            if path in nodes:raise ValueError('Duplicate FDT node')
            nodes[path]={}
        elif token==2:
            if not stack:raise ValueError('Unbalanced FDT')
            stack.pop()
        elif token==3:
            if not stack or cursor+8>end:raise ValueError('Invalid FDT property')
            length,name=struct.unpack_from('>2I',dtb,cursor);cursor+=8
            if cursor+length>end or name>=string_size:raise ValueError('FDT property outside range')
            stop=dtb.find(b'\0',strings+name,strings+string_size)
            if stop<0:raise ValueError('Unterminated FDT key')
            key=dtb[strings+name:stop].decode('ascii')
            path='/'+'/'.join(x for x in stack if x)
            if key in nodes[path]:raise ValueError('Duplicate FDT key')
            nodes[path][key]=(cursor,dtb[cursor:cursor+length])
            cursor=(cursor+length+3)&~3
        elif token==4:
            pass
        elif token==9:
            if stack:raise ValueError('Unbalanced FDT end')
            return nodes
        else:
            raise ValueError('Invalid FDT token')
    raise ValueError('Missing FDT end')

def qcdt_nodes(tree):
    if tree[:4]!=b'QCDT' or struct.unpack_from('<2I',tree,4)!=(2,1):raise ValueError('Expected single-entry A37 QCDT v2')
    start=tree.find(b'\xd0\x0d\xfe\xed')
    if start!=2048:raise ValueError('Unexpected DTB position')
    total=struct.unpack_from('>I',tree,start+4)[0]
    if total<40 or start+total>len(tree):raise ValueError('Unexpected A37 DTB size')
    return start,properties(tree[start:start+total])

def patch_low_cpu_corner(tree):
    start,nodes=qcdt_nodes(tree)
    def node_named(name):
        paths=[p for p,a in nodes.items() if a.get('regulator-name',(0,b''))[1]==name+b'\0']
        if len(paths)!=1:raise ValueError('Regulator missing or ambiguous')
        return paths[0]
    cpr=node_named(b'apc_corner')
    supply=nodes[cpr]['vdd-apc-supply'][1]
    rails=[p for p,a in nodes.items() if any(a.get(key,(0,b''))[1]==supply for key in ['phandle','linux,phandle'])]
    if len(rails)!=1:raise ValueError('CPU supply missing or ambiguous')
    s2=rails[0]
    if nodes[s2]['regulator-name'][1]!=b'8916_s2\0' or nodes[s2]['compatible'][1]!=b'qcom,spm-regulator\0':raise ValueError('Unexpected CPU supply')
    def value(node,key):return nodes[node][key][1]
    if value(cpr,'qcom,cpr-corner-map')!=struct.pack('>8I',1,1,2,2,3,3,3,3):raise ValueError('Unexpected CPU corner map')
    if value(cpr,'qcom,cpr-apc-volt-step')!=struct.pack('>I',12500):raise ValueError('Unexpected regulator step')
    expected={
      (cpr,'qcom,cpr-voltage-floor'):struct.pack('>3I',1050000,1050000,1162500),
      (cpr,'qcom,cpr-voltage-ceiling'):struct.pack('>3I',1050000,1150000,1350000),
      (s2,'regulator-min-microvolt'):struct.pack('>I',1050000),
    }
    patched=bytearray(tree);cells=[];allowed=set()
    for (node,key),old in expected.items():
        offset,data=nodes[node][key]
        if data!=old:raise ValueError('Unexpected base voltage: '+key)
        offset+=start
        struct.pack_into('>I',patched,offset,1037500)
        allowed.update(range(offset,offset+4))
        cells.append({'node':node,'property':key,'offset':offset,'from_uv':1050000,'to_uv':1037500})
    if len(patched)!=len(tree) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(tree,patched))):raise ValueError('Unrelated DT bytes changed')
    return bytes(patched),{'profile':'a37-low-cpu-12m5','cells':cells}

def patch_active_cpu_floors(tree):
    start,nodes=qcdt_nodes(tree)
    paths=[p for p,a in nodes.items() if a.get('regulator-name',(0,b''))[1]==b'apc_corner\0']
    if len(paths)!=1:raise ValueError('CPR node missing or ambiguous')
    node=paths[0];offset,value=nodes[node]['qcom,cpr-voltage-floor']
    if value!=struct.pack('>3I',1037500,1050000,1162500):raise ValueError('Expected E009 CPU floors')
    if nodes[node]['qcom,cpr-apc-volt-step'][1]!=struct.pack('>I',12500):raise ValueError('Unexpected regulator step')
    patched=bytearray(tree);cells=[];allowed=set()
    for index,old,new in [(1,1050000,1037500),(2,1162500,1150000)]:
        position=start+offset+index*4
        struct.pack_into('>I',patched,position,new)
        allowed.update(range(position,position+4))
        cells.append({'node':node,'property':'qcom,cpr-voltage-floor','offset':position,'from_uv':old,'to_uv':new})
    if len(patched)!=len(tree) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(tree,patched))):raise ValueError('Unrelated DT bytes changed')
    return bytes(patched),{'profile':'a37-active-cpu-12m5','cells':cells}

def patch_cpu_plan(tree):
    start,nodes=qcdt_nodes(tree)
    total=struct.unpack_from('>I',tree,start+4)[0]
    if total!=207477:raise ValueError('Expected preserved E010 DTB')
    dtb=bytearray(tree[start:start+total])
    cpr=[p for p,a in nodes.items() if a.get('regulator-name',(0,b''))[1]==b'apc_corner\0']
    clocks=[p for p,a in nodes.items() if b'qcom,clock-a53-8916\0' in a.get('compatible',(0,b''))[1]]
    if len(cpr)!=1 or len(clocks)!=1:raise ValueError('CPU nodes missing or ambiguous')
    cpr=cpr[0];clock=clocks[0]
    name='qcom,cpr-virtual-corner-quotient-adjustment'
    if name in nodes[cpr]:raise ValueError('CPU target adjustment already present')
    if nodes[cpr]['qcom,cpr-voltage-floor'][1]!=struct.pack('>3I',1037500,1037500,1150000):raise ValueError('Expected E010 floors')
    changes=[]
    def word(node,key,index,old,new):
        offset,data=nodes[node][key]
        if struct.unpack_from('>I',data,index*4)[0]!=old:raise ValueError('Unexpected CPU rate')
        struct.pack_into('>I',dtb,offset+index*4,new)
        changes.append({'node':node,'property':key,'index':index,'from':old,'to':new})
    keys=['qcom,speed0-bin-v0','qcom,speed1-bin-v0','qcom,speed3-bin-v0',
          'qcom,speed0-bin-v1','qcom,speed2-bin-v1','qcom,speed3-bin-v1']
    for key in keys:
        if struct.unpack_from('>I',nodes[clock][key][1],28)[0]!=3:raise ValueError('Unexpected 533 MHz corner')
        word(clock,key,6,533333000,533333333)
    word(cpr,'qcom,cpr-corner-frequency-map',5,533330000,533333333)
    header=list(struct.unpack_from('>10I',dtb))
    strings=header[3];structure=header[2]
    if strings+header[8]!=total or structure+header[9]>strings:raise ValueError('Review FDT layout')
    insertion=nodes[cpr]['qcom,cpr-voltage-floor'][0]-12
    if not structure<=insertion<structure+header[9] or struct.unpack_from('>I',dtb,insertion)[0]!=3:raise ValueError('Invalid property insertion point')
    encoded_name=name.encode()+b'\0'
    value=struct.pack('>8i',0,0,0,0,0,-26,-20,-13)
    token=struct.pack('>3I',3,len(value),header[8])+value
    rebuilt=bytearray(dtb[:insertion]+token+dtb[insertion:]+encoded_name)
    header[1]=len(rebuilt);header[3]+=len(token);header[8]+=len(encoded_name);header[9]+=len(token)
    struct.pack_into('>10I',rebuilt,0,*header)
    if start+len(rebuilt)>len(tree) or any(tree[start+total:]):raise ValueError('Insufficient clean QCDT padding')
    entries=[p for p in range(12,start-7,4) if struct.unpack_from('<2I',tree,p)==(start,total)]
    if len(entries)!=1:raise ValueError('QCDT size field missing or ambiguous')
    result=bytearray(tree)
    struct.pack_into('<I',result,entries[0]+4,len(rebuilt))
    result[start:start+len(rebuilt)]=rebuilt
    after=properties(rebuilt)
    if after.keys()!=nodes.keys():raise ValueError('FDT nodes changed')
    expected={(c['node'],c['property']) for c in changes}
    for node,props in nodes.items():
        if set(after[node])!=set(props)|({name} if node==cpr else set()):raise ValueError('FDT property set changed')
        for key,(_,data) in props.items():
            actual=after[node][key][1]
            if (node,key) not in expected and actual!=data:raise ValueError('Unrelated FDT payload changed')
    if after[cpr][name][1]!=value:raise ValueError('Target trim differs')
    return bytes(result),{'profile':'a37-cpu-plan-e011','cells':changes,'new_property':name,
                          'dtb_bytes':len(rebuilt),'trim_counts':[0,0,0,0,0,26,20,13]}

def patch_cpu_efficiency_e012(tree):
    start,nodes=qcdt_nodes(tree)
    cpr=[p for p,a in nodes.items() if a.get('regulator-name',(0,b''))[1]==b'apc_corner\0']
    if len(cpr)!=1:raise ValueError('CPR node missing or ambiguous')
    cpr=cpr[0];supply=nodes[cpr]['vdd-apc-supply'][1]
    rails=[p for p,a in nodes.items() if any(a.get(key,(0,b''))[1]==supply for key in ['phandle','linux,phandle'])]
    if len(rails)!=1:raise ValueError('CPU supply missing or ambiguous')
    s2=rails[0]
    if nodes[s2]['regulator-name'][1]!=b'8916_s2\0':raise ValueError('Unexpected CPU supply')
    expected={
      (cpr,'qcom,cpr-voltage-floor'):struct.pack('>3I',1037500,1037500,1150000),
      (cpr,'qcom,cpr-voltage-ceiling'):struct.pack('>3I',1037500,1150000,1350000),
      (s2,'regulator-min-microvolt'):struct.pack('>I',1037500),
      (cpr,'qcom,cpr-virtual-corner-quotient-adjustment'):struct.pack('>8i',0,0,0,0,0,-26,-20,-13),
    }
    patched=bytearray(tree);cells=[];allowed=set()
    for (node,key),old in expected.items():
        offset,data=nodes[node][key]
        if data!=old:raise ValueError('Expected E011 CPU plan: '+key)
        is_target=key=='qcom,cpr-virtual-corner-quotient-adjustment'
        index=7 if is_target else 0
        old_value=-13 if is_target else 1037500
        new_value=-39 if is_target else 1025000
        offset+=start+index*4
        struct.pack_into('>i' if is_target else '>I',patched,offset,new_value)
        allowed.update(range(offset,offset+4))
        cells.append({'node':node,'property':key,'offset':offset,'from':old_value,'to':new_value})
    if len(patched)!=len(tree) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(tree,patched))):raise ValueError('Unrelated DT bytes changed')
    return bytes(patched),{'profile':'a37-cpu-efficiency-e012','cells':cells}

def patch_cpu_targets_e013(tree):
    start,nodes=qcdt_nodes(tree)
    matches=[p for p,a in nodes.items() if a.get('regulator-name',(0,b''))[1]==b'apc_corner\0']
    if len(matches)!=1:raise ValueError('CPR node missing or ambiguous')
    node=matches[0];key='qcom,cpr-virtual-corner-quotient-adjustment'
    if nodes[node]['qcom,cpr-voltage-floor'][1]!=struct.pack('>3I',1025000,1037500,1150000):raise ValueError('Expected E012 voltage limits')
    offset,value=nodes[node][key]
    if value!=struct.pack('>8i',0,0,0,0,0,-26,-20,-39):raise ValueError('Expected E012 CPU targets')
    counts=[0,0,-39,-39,0,-65,-43,-65]
    replacement=struct.pack('>8i',*counts)
    patched=bytearray(tree);offset+=start
    patched[offset:offset+len(value)]=replacement
    if len(patched)!=len(tree) or any(a!=b and not offset<=i<offset+len(value) for i,(a,b) in enumerate(zip(tree,patched))):raise ValueError('Unrelated DT bytes changed')
    return bytes(patched),{'profile':'a37-cpu-targets-e013','node':node,'property':key,'offset':offset,'counts':counts}
