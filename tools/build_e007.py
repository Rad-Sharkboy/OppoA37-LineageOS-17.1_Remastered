#!/usr/bin/env python3
"""Build E007 from explicitly pinned inputs; V2.1 defaults remain pinned separately."""
from build_v21 import main
from pathlib import Path

E007_HAL_SHA = '36da00a282d6a03ac51bc58b7382b1f7548027071e95a58a0a7fbaabdc86c9c5'

if __name__ == '__main__':
    main(release='V2.1 E007',
         archive_name='Lineage_17.1_REMASTERED_V2.1_E007.zip',
         kernel_sha='33800a510a7edf5d0e4b2c0746dc91afdbce2b3533c9d3f7e4d4c3ad3097cec2',
         hal_sha=E007_HAL_SHA,
         kernel_commit='8d94be23b5e760bd403cf663ffcd677df1be83a3',
         scripts=Path(__file__).resolve().parent/'e007')
