"""Apply verified native NPC transparency and correct wide-sheet dimensions."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def apply(layer):
    folder=ROOT/'tools/hoenn/data/extra-gyms/sprites';manifest=json.loads((folder/'sources.json').read_text())
    for row in manifest['records']:
        key=row['key'];p=folder/row['file'];pal=p.with_suffix('.pal')
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        assert hashlib.sha256(pal.read_bytes()).hexdigest()==row['palette_sha256']
        for f in [p,pal]:layer.stage('graphics/object_events/pics/people/journey_pwt_'+key.lower()+f.suffix,f.read_bytes())
    def raw(p):return (layer.outputs[p] if p in layer.outputs else (layer.source/p).read_bytes()).decode()
    p='src/data/object_events/object_event_graphics_info.h';text=raw(p)
    for key in ['CANDICE','VALERIE']:
        pattern=r'(const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyPWT'+key+r' = \{)(.*?)(\};)'
        def wide(m):
            body=m[2].replace('.size=256','.size=512').replace('.width=16','.width=32').replace('gObjectEventBaseOam_16x32','gObjectEventBaseOam_32x32').replace('sOamTables_16x32','sOamTables_32x32')
            return m[1]+body+m[3]
        text,count=re.subn(pattern,wide,text);assert count==1
    layer.stage(p,text)
    p='src/data/object_events/object_event_pic_tables.h';text=raw(p)
    for key in ['CANDICE','VALERIE']:
        text,count=re.subn(r'(sPicTable_JourneyPWT'+key+r'\[\] = \{ overworld_ascending_frames\(gObjectEventPic_JourneyPWT'+key+r', )[24](, 4\) \};)',r'\g<1>4\2',text);assert count==1
    layer.stage(p,text)
    return manifest
