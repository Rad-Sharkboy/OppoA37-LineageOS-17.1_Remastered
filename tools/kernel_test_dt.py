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

def patch_low_cpu_corner(tree):
    if tree[:4]!=b'QCDT' or struct.unpack_from('<2I',tree,4)!=(2,1):raise ValueError('Expected single-entry A37 QCDT v2')
    start=tree.find(b'\xd0\x0d\xfe\xed')
    if start!=2048:raise ValueError('Unexpected DTB position')
    total=struct.unpack_from('>I',tree,start+4)[0]
    if total!=207477 or start+total>len(tree):raise ValueError('Unexpected A37 DTB size')
    dtb=tree[start:start+total];nodes=properties(dtb)
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
