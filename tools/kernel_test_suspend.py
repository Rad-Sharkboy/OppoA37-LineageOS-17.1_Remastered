"""Add the source-built A37 suspend level to the installed QCDT."""
import struct

from kernel_test_dt import properties, qcdt_nodes


CLUSTER = '/soc/qcom,lpm-levels/qcom,pm-cluster@0'
PREVIOUS = CLUSTER + '/qcom,pm-cluster-level@1'
LEVEL = CLUSTER + '/qcom,pm-cluster-level@2'
L2_PROGRAM = bytes.fromhex('0032b010e0d06bc0425111070141b0504e0202c0d012e06b0232500f')


def cell(value):
    return struct.pack('>I', value)


def padded(data):
    return data + bytes(-len(data) % 4)


def values(node):
    return {key: value for key, (_, value) in node.items()}


def patch_suspend_level(tree, board):
    start, original = qcdt_nodes(tree)
    chip, platform, subtype, soc_rev, board_id, offset, length = struct.unpack_from('<7I', tree, 12)
    if (chip, platform, subtype, soc_rev, board_id, offset) != (206, 8, 0, 0, 15399, start):
        raise ValueError('Unexpected A37 QCDT entry')
    dtb = tree[start:start + length]
    header = list(struct.unpack_from('>10I', dtb))
    if header[1] != length or header[2] + header[9] != header[3] or header[3] + header[8] != length:
        raise ValueError('Unexpected A37 FDT sections')
    source = properties(board)
    spm = '/soc/qcom,spm@b012000'
    mpm = '/soc/qcom,mpm@601d0'
    for nodes in (source, original):
        if (nodes[spm]['qcom,saw2-spm-cmd-pc'][1] != L2_PROGRAM or
                nodes[spm]['qcom,name'][1] != b'system-l2\0' or
                nodes[CLUSTER + '/qcom,pm-cluster-level@0']['qcom,spm-l2-mode'][1] != b'active\0' or
                nodes[PREVIOUS]['qcom,spm-l2-mode'][1] != b'gdhs\0' or
                nodes[CLUSTER + '/qcom,pm-cpu/qcom,pm-cpu-level@2']['qcom,spm-cpu-mode'][1] != b'pc\0' or
                not all(nodes[mpm][key][1] for key in ('qcom,gic-map', 'qcom,gpio-map'))):
            raise ValueError('Missing board suspend or wake support')
    expected = {'reg': cell(2), 'label': b'l2-pc\0', 'qcom,spm-l2-mode': b'pc\0',
                'qcom,latency-us': cell(11030), 'qcom,ss-power': cell(490),
                'qcom,energy-overhead': cell(972390), 'qcom,time-overhead': cell(1580),
                'qcom,min-child-idx': cell(2), 'qcom,notify-rpm': b'', 'qcom,suspend-only': b''}
    if LEVEL in original or values(source[LEVEL]) != expected:
        raise ValueError('Unexpected source or installed cluster level')
    end = max(position + len(value) for position, value in original[PREVIOUS].values())
    end = (end + 3) & ~3
    if dtb[end:end + 4] != cell(2):
        raise ValueError('Previous cluster level must be a leaf')
    insert = end + 4
    strings = bytearray(dtb[header[3]:])
    node = bytearray(cell(1) + padded(LEVEL.rsplit('/', 1)[1].encode() + b'\0'))
    for key, data in values(source[LEVEL]).items():
        name = key.encode() + b'\0'
        index = strings.find(name)
        if index < 0:
            index = len(strings)
            strings.extend(name)
        node.extend(struct.pack('>3I', 3, len(data), index) + padded(data))
    node.extend(cell(2))
    result = bytearray(dtb[:insert] + node + dtb[insert:header[3]] + strings)
    if start + len(result) > len(tree) or any(tree[start + length:]):
        raise ValueError('Insufficient empty QCDT padding')
    header[1] = len(result)
    header[3] += len(node)
    header[8] = len(strings)
    header[9] += len(node)
    struct.pack_into('>10I', result, 0, *header)
    patched = bytearray(tree)
    struct.pack_into('<I', patched, 36, len(result))
    patched[start:start + len(result)] = result
    _, actual = qcdt_nodes(patched)
    if set(actual) != set(original) | {LEVEL} or values(actual[LEVEL]) != expected:
        raise ValueError('New suspend level differs')
    if any(values(actual[path]) != values(props) for path, props in original.items()):
        raise ValueError('An existing hardware property changed')
    return bytes(patched), {'profile': 'a37-suspend-e024v3', 'node': LEVEL,
                            'scope': 'system suspend', 'latency_us': 11030}
