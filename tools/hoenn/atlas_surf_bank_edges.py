"""Audit actual C marine-bank translation on both cameras of source seams.

This compiles only the extracted source helpers on the host, with authenticated
native attributes, eight-word metatiles, RGB555 palettes and symbolic pointer
identities. It does not compile a game or change a bank/runtime. Equal graphics
bytes in different C arrays do not establish pointer equality.
"""
import argparse
from collections import Counter
import ctypes as C
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from atlas_surf_source import CARDINAL, OPPOSITE


def _clean(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def _braced(text, opening):
    depth = 1
    for end in range(opening+1,len(text)):
        depth += (text[end]=='{')-(text[end]=='}')
        if depth == 0:return text[opening+1:end]
    raise ValueError('Unclosed native C initializer')


def _definition(text,name):
    match=re.search(r'(?m)^(?:static\s+)?(?:bool8|bool32|u16|u32)\s+'
                    +re.escape(name)+r'\s*\([^;{}]*\)\s*\{',text)
    if not match:raise ValueError(('Actual native helper missing',name))
    start=text.index('{',match.start())
    return text[match.start():start+1]+_braced(text,start)+'}'


def rgb555_palette(raw):
    """Match native JASC→GBA truncation; RGB24 equality is the wrong test."""
    lines=raw.decode().splitlines()
    if lines[:2] != ['JASC-PAL','0100'] or len(lines)<3:
        raise ValueError('Invalid native JASC palette')
    count=int(lines[2]); colors=[list(map(int,line.split())) for line in lines[3:] if line.strip()]
    if len(colors)!=count or count!=16 or any(len(row)!=3 or any(not 0<=v<=255 for v in row) for row in colors):
        raise ValueError('Native palette must contain exactly sixteen RGB colors')
    return struct.pack('<16H',*((r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in colors))


class _Tileset(C.Structure):
    _fields_=[('tiles',C.c_void_p),('palettes',C.c_void_p),('metatiles',C.POINTER(C.c_uint16)),
              ('metatileAttributes',C.POINTER(C.c_uint16)),('callback',C.c_void_p)]


class _Layout(C.Structure):
    _fields_=[('isFrlg',C.c_uint8),('primaryTileset',C.POINTER(_Tileset)),('secondaryTileset',C.POINTER(_Tileset))]


class Banks:
    """Read all assets through the logical source, never a disk fallback."""
    def __init__(self,inputs):
        self.inputs=inputs
        self.headers=_clean(inputs.read('src/data/tilesets/headers.h').decode())
        self.metas=_clean(inputs.read('src/data/tilesets/metatiles.h').decode())
        self.graphics=_clean(inputs.read('src/data/tilesets/graphics.h').decode())
        # The Emerald primary General arrays are defined in graphics.c,
        # unlike the secondary banks and FRLG primary. Read the logical
        # translation unit too; do not infer its paths from another bank.
        try:self.graphics+='\n'+_clean(inputs.read('src/graphics.c').decode())
        except FileNotFoundError:pass
        self.text='\n'.join((self.headers,self.metas,self.graphics))
        self.callbacks=_clean(inputs.read('src/tileset_anims.c').decode())
        self.cache={};self.arrays={};self.tokens={};self.layouts={};self.buffers=[];self.alias_cache={}

    def alias(self,name):
        if name in self.alias_cache:return self.alias_cache[name]
        seen=set()
        while True:
            if name in seen:raise ValueError(('Cyclic C pointer alias',name))
            seen.add(name)
            match=re.search(r'^\s*#define\s+'+re.escape(name)+r'\s+\(?([A-Za-z_]\w*)\)?\s*$',self.text,re.M)
            if match is None:
                match=re.search(r'\b'+re.escape(name)+r'\b[^;\n]*__attribute__\s*\(\(\s*alias\("(\w+)"\)',self.text)
            if match is None:
                for symbol in seen:self.alias_cache[symbol]=name
                return name
            name=match[1]

    def array(self,name):
        name=self.alias(name)
        if name in self.arrays:return self.arrays[name]
        match=re.search(r'\b(u8|u16|u32)(?:\s+ALIGNED\(\d+\))?\s+'+re.escape(name)+r'\s*(?:\[[^]]*\])+\s*=\s*',self.text)
        if match is None:raise ValueError(('Native asset array definition missing',name))
        at=match.end()
        if self.text[at]=='{':body=_braced(self.text,at)
        else:body=self.text[at:self.text.index(';',at)]
        paths=re.findall(r'INCBIN_\w+\("([^"\n]+)"\)',body)
        if paths:
            residue=re.sub(r'INCBIN_\w+\("[^"\n]+"\)|[\s,{}]','',body)
            if residue:raise ValueError(('Mixed or unmodelled asset initializer',name,residue))
            raw=bytearray();assets=[]
            for path in paths:
                try:data=self.inputs.read(path); actual=path
                except FileNotFoundError:
                    if path.endswith('.gbapal'):
                        actual=path[:-7]+'.pal'; data=rgb555_palette(self.inputs.read(actual))
                    elif '.4bpp' in path:
                        actual=re.sub(r'\.4bpp(?:\.[\w]+)*$','.png',path)
                        if actual==path:raise ValueError(('Unresolved native graphic',path))
                        data=self.inputs.read(actual)
                    else:raise
                raw.extend(data);assets.append(dict(path=actual,sha256=hashlib.sha256(data).hexdigest()))
            result=dict(symbol=name,raw=bytes(raw),assets=assets)
        else:
            tokens=[v.strip() for v in re.sub(r'[{}]','',body).split(',') if v.strip()]
            if any(not re.fullmatch(r'(?:0x[0-9a-fA-F]+|\d+)[uUlL]*',v) for v in tokens):
                raise ValueError(('Nonliteral native asset initializer',name))
            width=int(match[1][1:]);values=[int(re.sub(r'[uUlL]+$','',v),0) for v in tokens]
            raw=struct.pack('<'+{8:'B',16:'H',32:'I'}[width]*len(values),*values)
            result=dict(symbol=name,raw=raw,assets=[])
        self.arrays[name]=result
        return result

    def token(self,name):
        name=self.alias(name)
        if name=='NULL':return None
        if name not in self.tokens:
            self.tokens[name]=C.create_string_buffer(1)
        return C.addressof(self.tokens[name])

    def bank(self,name):
        name=self.alias(name)
        if name in self.cache:return self.cache[name]
        match=re.search(r'\bconst struct Tileset\s+'+re.escape(name)+r'\s*=\s*\{',self.headers)
        if not match:raise ValueError(('Native bank header missing',name))
        body=_braced(self.headers,match.end()-1)
        fields={key:self.alias(value) for key,value in re.findall(r'\.(tiles|palettes|metatiles|metatileAttributes|callback)\s*=\s*(\w+)\s*(?=[,}])',body+',')}
        if set(fields)!={'tiles','palettes','metatiles','metatileAttributes','callback'}:
            raise ValueError(('Native bank fields require explicit pointer symbols',name,fields))
        callback=fields['callback']
        if callback!='NULL' and not re.search(r'\b'+re.escape(callback)+r'\s*\([^;{}]*\)\s*\{',self.callbacks):
            raise ValueError(('Native animation callback definition unavailable',callback))
        arrays={field:self.array(fields[field]) for field in ('tiles','palettes','metatiles','metatileAttributes')}
        raw=arrays['palettes']['raw']
        if len(raw)!=16*16*2:raise ValueError(('Bank needs all sixteen native palette rows',name,len(raw)))
        palette=C.create_string_buffer(raw);metas=C.create_string_buffer(arrays['metatiles']['raw']);attrs=C.create_string_buffer(arrays['metatileAttributes']['raw'])
        self.buffers.extend((palette,metas,attrs))
        native=_Tileset(self.token(fields['tiles']),C.addressof(palette),C.cast(metas,C.POINTER(C.c_uint16)),
                        C.cast(attrs,C.POINTER(C.c_uint16)),self.token(callback))
        record=dict(name=name,fields=fields,arrays=arrays,native=native,pointer=C.pointer(native))
        self.cache[name]=record
        return record

    def layout(self,name):
        row=self.inputs.layout(name)
        key=(row['layout_version'],row['primary_tileset'],row['secondary_tileset'])
        if key not in self.layouts:
            a,b=(self.bank(row[field]) for field in ('primary_tileset','secondary_tileset'))
            self.layouts[key]=_Layout(key[0]=='frlg',a['pointer'],b['pointer'])
        return self.layouts[key]

    def detail(self,first,second,word):
        """Safe pointer/array checks and diagnostic for same-format C compares."""
        a,b=self.inputs.layout(first),self.inputs.layout(second)
        if a['layout_version']!=b['layout_version']:return dict(reason='cross-format-helper-rule')
        cutoff,size=(640,4) if a['layout_version']=='frlg' else (512,2)
        mid=word&1023;field='primary_tileset' if mid<cutoff else 'secondary_tileset';index=mid if mid<cutoff else mid-cutoff
        ba,bb=self.bank(a[field]),self.bank(b[field])
        for bank in (ba,bb):
            if len(bank['arrays']['metatileAttributes']['raw'])<(index+1)*size or len(bank['arrays']['metatiles']['raw'])<(index+1)*16:
                return dict(reason='metatile-outside-native-bank',unsafe_native_read=True,bank=bank['name'],index=index)
        aa=ba['arrays']['metatileAttributes']['raw'][index*size:(index+1)*size]
        ab=bb['arrays']['metatileAttributes']['raw'][index*size:(index+1)*size]
        if aa!=ab:return dict(reason='full-metatile-attributes-differ',attributes=[int.from_bytes(aa,'little'),int.from_bytes(ab,'little')])
        wa=ba['arrays']['metatiles']['raw'][index*16:(index+1)*16];wb=bb['arrays']['metatiles']['raw'][index*16:(index+1)*16]
        if wa!=wb:return dict(reason='eight-metatile-words-differ',words=[list(struct.unpack('<8H',wa)),list(struct.unpack('<8H',wb))])
        for tile in struct.unpack('<8H',wa):
            ta,tb=(self.bank(row['primary_tileset' if (tile&1023)<cutoff else 'secondary_tileset']) for row in (a,b))
            if ta['fields']['tiles']!=tb['fields']['tiles']:
                return dict(reason='tiles-pointer-symbols-differ',symbols=[ta['fields']['tiles'],tb['fields']['tiles']],
                    source_bytes_equal=ta['arrays']['tiles']['raw']==tb['arrays']['tiles']['raw'],
                    byte_equality_does_not_prove_pointer_identity=True)
            if ta['fields']['callback']!=tb['fields']['callback']:
                return dict(reason='animation-callback-pointers-differ',callbacks=[ta['fields']['callback'],tb['fields']['callback']])
            palette=tile>>12;palcut=7 if cutoff==640 else 6
            pa,pb=(self.bank(row['primary_tileset' if palette<palcut else 'secondary_tileset']) for row in (a,b))
            ca=pa['arrays']['palettes']['raw'][palette*32:(palette+1)*32];cb=pb['arrays']['palettes']['raw'][palette*32:(palette+1)*32]
            if ca!=cb:return dict(reason='palette-rgb555-differs',palette=palette,colors=[list(struct.unpack('<16H',ca)),list(struct.unpack('<16H',cb))])
        return dict(reason='same-format-complete-native-bank-match')


class CompiledMarineView:
    def __init__(self,inputs):
        self.inputs=inputs;self.banks=Banks(inputs);self.cache={}
        field=inputs.read('src/fieldmap.c').decode()
        names=('GetNumMetatilesInPrimary','GetNumPalsInPrimary','JourneyMarineViewGroup',
               'JourneyMarineViewMap','JourneyMarineTranslateBlock','JourneyMarineViewCompatible','JourneyAtlasPhysicalWord')
        definitions={name:_definition(field,name) for name in names}
        atlas_group=''
        if 'JourneyAtlasGroup(' in definitions['JourneyMarineViewGroup']:
            runtime=inputs.read('src/data/journey_atlas_runtime.h').decode()
            definition=_definition(runtime,'JourneyAtlasGroup')
            group_struct=re.search(r'struct JourneyAtlasGroupRange\s*\{[^}]+\};',runtime)
            group_table=re.search(r'static const struct JourneyAtlasGroupRange sAtlasGroups\[\]\s*=\s*\{',runtime)
            base=re.search(r'^#define JOURNEY_ATLAS_GROUP_BASE\s+\d+\s*$',runtime,re.M)
            if not group_struct or not group_table or not base:
                raise ValueError('Actual Atlas group predicate lacks its bound runtime table')
            atlas_group=(group_struct[0]+'\nstatic const struct JourneyAtlasGroupRange sAtlasGroups[]={'
                         +_braced(runtime,group_table.end()-1)+'};\n'+base[0]+'\n'+definition+'\n')
            definitions['JourneyAtlasGroup']=definition
        self.helper_sha256={name:hashlib.sha256(value.encode()).hexdigest() for name,value in definitions.items()}
        constants=inputs.read('include/fieldmap.h').decode()+inputs.read('include/global.fieldmap.h').decode()
        for name,expected in (('NUM_METATILES_IN_PRIMARY_FRLG',640),('NUM_METATILES_IN_PRIMARY',512),
                              ('NUM_PALS_IN_PRIMARY_FRLG',7),('NUM_PALS_IN_PRIMARY',6),
                              ('NUM_TILES_PER_METATILE',8),('MAPGRID_METATILE_ID_MASK',1023),
                              ('MAPGRID_COLLISION_MASK',3072)):
            match=re.search(r'^\s*#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+|\d+)\b',constants,re.M)
            if match is None or int(match[1],0)!=expected:
                raise ValueError(('Native bank geometry/mask constant changed; review audit model',name))
        defines='\n'.join(re.findall(r'^\s*#define\s+(?:NUM_METATILES_IN_PRIMARY(?:_FRLG)?|NUM_PALS_IN_PRIMARY(?:_FRLG)?|NUM_TILES_PER_METATILE|MAPGRID_METATILE_ID_MASK|MAPGRID_COLLISION_MASK)\s+[^\n]+',constants,re.M))
        global_h=_clean(inputs.read('include/constants/global.h').decode())
        match=re.search(r'enum Connection\s*\{',global_h)
        if not match:raise ValueError('Native connection enum missing')
        enum='enum Connection {'+_braced(global_h,match.end()-1)+'};'
        types=_clean(inputs.read('include/constants/map_types.h').decode())
        match=re.search(r'enum MapType\s*\{',types)
        if not match:raise ValueError('Native map-type enum missing')
        enum+='\nenum MapType {'+_braced(types,match.end()-1)+'};'
        map_types=sorted(set(row['map_type'] for row in inputs.maps.values()))
        symbols=set(re.findall(r'MAP_GROUP\((MAP_\w+)\)','\n'.join(definitions.values())))
        ids={row['id']:inputs.identities[name] for name,row in inputs.maps.items() if name in inputs.identities}
        maps='\n'.join(f'#define {symbol} {ids[symbol]}' for symbol in sorted(symbols))
        code=r'''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef int32_t s32;typedef uint8_t bool8;
#define TRUE 1
#define FALSE 0
#define MAP_GROUP(map) ((map)>>8)
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
struct Tileset {const void *tiles;const u16 (*palettes)[16];const u16 *metatiles;const u16 *metatileAttributes;const void *callback;};
struct MapLayout {u8 isFrlg;const struct Tileset *primaryTileset,*secondaryTileset;};
struct MapConnection {int direction,mapGroup;};
struct MapConnections {int count;const struct MapConnection *connections;};
struct MapHeader {int mapType;const struct MapLayout *mapLayout;const struct MapConnections *connections;};
struct Tileset gTileset_JourneySeviiSea;
static struct MapHeader gMapHeader;
static struct {struct {int mapGroup;} location;} save;
#define gSaveBlock1Ptr (&save)
'''+defines+'\n'+enum+'\n'+maps+'\n'+atlas_group+'\n'+'\n'.join(value for key,value in definitions.items() if key!='JourneyAtlasGroup')+r'''
int marine_view(const struct MapLayout *from,const struct MapLayout *to,int mapType,int group,const int *groups,int count,u16 block,u16 *out) {
 struct MapConnection links[256];struct MapConnections connections={count,links};
 if(count<0||count>256)return -1;
 for(int i=0;i<count;i++){links[i].direction=CONNECTION_SOUTH;links[i].mapGroup=groups[i];}
 gMapHeader.mapType=mapType;gMapHeader.mapLayout=to;gMapHeader.connections=&connections;
 save.location.mapGroup=group;
 return JourneyAtlasPhysicalWord(from,block,out);
}
'''
        code+='\nint marine_type(int index){static const int values[]={'+','.join(map_types)+'};return values[index];}\n'
        compiler=shutil.which('cc') or shutil.which('gcc')
        if not compiler:raise RuntimeError('Host C compiler required to audit actual bank helpers')
        with tempfile.TemporaryDirectory(prefix='atlas-bank-helper-') as temp:
            path=Path(temp)/'helper.c';library=Path(temp)/'helper.so';path.write_text(code)
            result=subprocess.run([compiler,'-std=gnu17','-Wall','-Wextra','-Werror','-O0','-shared','-fPIC',str(path),'-o',str(library)],capture_output=True,text=True)
            if result.returncode:raise ValueError(('Actual native bank helper compilation failed',result.stderr))
            self.native=C.CDLL(str(library))
        self.native.marine_view.argtypes=[C.POINTER(_Layout),C.POINTER(_Layout),C.c_int,C.c_int,C.POINTER(C.c_int),C.c_int,C.c_uint16,C.POINTER(C.c_uint16)]
        self.native.marine_view.restype=C.c_int
        self.map_types={name:self.native.marine_type(i) for i,name in enumerate(map_types)}
        # The actual helper compares this special header's address. Preserve
        # that identity instead of substituting its equal fields as a pointer.
        try:sea=self.banks.bank('gTileset_JourneySeviiSea')
        except ValueError:sea=None
        if sea is not None:
            special=_Tileset.in_dll(self.native,'gTileset_JourneySeviiSea')
            C.memmove(C.addressof(special),C.addressof(sea['native']),C.sizeof(_Tileset))
            sea['pointer']=C.pointer(special);self.banks.buffers.append(special)

    def check(self,first,second,word):
        key=first,second,word
        if key in self.cache:return self.cache[key]
        before=self.inputs.layout(first);after=self.inputs.layout(second)
        detail=self.banks.detail(first,second,word)
        if detail.get('unsafe_native_read'):
            result=dict(compatible=False,**detail)
        else:
            a,b=self.banks.layout(first),self.banks.layout(second)
            groups=[self.inputs.identities[self.inputs.by_id[c['map']]]>>8
                    for c in self.inputs.maps[second].get('connections') or [] if c['direction'] in CARDINAL]
            array=(C.c_int*len(groups))(*groups);out=C.c_uint16(0xFFFF)
            accepted=self.native.marine_view(C.byref(a),C.byref(b),self.map_types[self.inputs.maps[second]['map_type']],
                self.inputs.identities[second]>>8,array,len(groups),word,C.byref(out))
            if accepted not in (0,1):raise ValueError('Native bank helper returned an invalid status')
            if accepted and out.value&~1023 != word&~1023:
                raise ValueError('Actual physical bank helper changed collision/elevation bits')
            result=dict(compatible=bool(accepted),translated_word=out.value if accepted else None,
                        physical_collision_height_preserved=bool(accepted),**detail)
            if before['layout_version']!=after['layout_version']:
                result['reason']='actual-cross-format-allowlist' if accepted else 'cross-format-metatile-not-allowed'
            elif bool(accepted)!=(detail['reason']=='same-format-complete-native-bank-match'):
                # Equal layouts bypass ViewCompatible intentionally. No other
                # discrepancy between the source model and actual C is hidden.
                same=all(before[k]==after[k] for k in ('layout_version','primary_tileset','secondary_tileset'))
                if not same:raise ValueError(('Native C and independent bank diagnostic disagree',key,detail,accepted))
        self.cache[key]=result
        return result


def _face(inputs,first,second,direction,offset,depth=0):
    a,b=inputs.layout(first),inputs.layout(second)
    horizontal=direction in ('left','right');axis='height' if horizontal else 'width'
    for value in range(max(0,offset),min(a[axis],offset+b[axis])):
        if horizontal:
            one=(a['width']-1-depth if direction=='right' else depth,value)
            two=(depth if direction=='right' else b['width']-1-depth,value-offset)
        else:
            one=(value,a['height']-1-depth if direction=='down' else depth)
            two=(value-offset,depth if direction=='down' else b['height']-1-depth)
        if all(0<=p[0]<layout['width'] and 0<=p[1]<layout['height'] for p,layout in ((one,a),(two,b))):
            yield one,two


def audit_edges(inputs,*,scope=None,prepared_sha256=None,halo_depth=7):
    """Whitelist only complete two-camera passable faces, never RGB guesses."""
    if not 1<=halo_depth<=7:raise ValueError('Native visual apron bound must be1..7')
    names=set(inputs.identities if scope is None else scope)
    compiled=CompiledMarineView(inputs)
    records=[];unproven=[];pairs=set();seen=set()
    for first in sorted(names):
        for link in inputs.maps[first].get('connections') or []:
            direction=link['direction'];second=inputs.by_id[link['map']]
            if direction not in CARDINAL or second not in names:continue
            offset=int(link['offset']);key=min((first,second,direction,offset),(second,first,OPPOSITE[direction],-offset))
            if key in seen:continue
            seen.add(key)
            reverse=[c for c in inputs.maps[second].get('connections') or [] if c['map']==inputs.maps[first]['id'] and c['direction']==OPPOSITE[direction] and int(c['offset'])==-offset]
            record=dict(first=first,second=second,direction=direction,offset=offset,
                        reciprocal=len(reverse)==1,passable_contacts=0,face_failures=[],halo_failures=[])
            first_layout,second_layout=inputs.layout(first),inputs.layout(second)
            record['same_bank_headers']=all(first_layout[k]==second_layout[k] for k in ('layout_version','primary_tileset','secondary_tileset'))
            failures={};halo={};word_cases={}
            try:
                for depth in range(halo_depth):
                    for one,two in _face(inputs,first,second,direction,offset,depth):
                        wa,wb=inputs.word(first,*one),inputs.word(second,*two)
                        passable=depth==0 and not (wa|wb)&0xC00
                        if passable:record['passable_contacts']+=1
                        for source,target,point,word in ((first,second,one,wa),(second,first,two,wb)):
                            case=compiled.check(source,target,word)
                            ck=(source,target,word)
                            if passable:word_cases[ck]=case
                            if not case['compatible']:
                                target_failures=failures if passable else halo
                                value=target_failures.setdefault(ck,dict(source_map=source,camera_map=target,word=word,
                                    sample=list(point),depth=depth,occurrences=0,**case))
                                value['occurrences']+=1
                record['face_failures']=list(failures.values());record['halo_failures']=list(halo.values())
                record['required_word_cases']=len(word_cases)
                record['both_cameras_face_compatible']=bool(record['passable_contacts']) and not failures and record['reciprocal']
                record['seven_tile_visual_report_compatible']=not halo and not failures
                if not record['both_cameras_face_compatible']:
                    unproven.append(dict(first=first,second=second,direction=direction,offset=offset,
                        reason='nonreciprocal' if not record['reciprocal'] else 'no-passable-face-contacts' if not record['passable_contacts'] else 'required-face-bank-incompatible',
                        passable_contacts=record['passable_contacts'],failures=record['face_failures']))
            except (ValueError,FileNotFoundError) as error:
                record['asset_or_source_error']=str(error);record['both_cameras_face_compatible']=False
                unproven.append(dict(first=first,second=second,reason='unresolved-native-bank-input',detail=str(error)))
            records.append(record)
    # The reachability consumer whitelists MAP PAIRS, not individual offsets.
    # A compatible east seam must never hide an incompatible north seam
    # between the same two maps. Authenticate their complete conjunction.
    by_pair={}
    for record in records:
        pair=tuple(sorted((record['first'],record['second'])))
        by_pair.setdefault(pair,[]).append(record)
    for (first,second),edges in by_pair.items():
        accepted=(sum(edge['passable_contacts'] for edge in edges)>0
                  and all(edge['reciprocal'] and not edge.get('asset_or_source_error')
                          and not edge['face_failures'] for edge in edges))
        if accepted:pairs.update(((first,second),(second,first)))
        for edge in edges:edge['pair_authenticated_across_all_connections']=accepted
    inputs.assert_unchanged()
    if hasattr(inputs,'layer'):
        actual={path:hashlib.sha256(raw).hexdigest() for path,raw in inputs.layer.outputs.items()}
        if prepared_sha256 is not None and prepared_sha256!=actual:
            raise ValueError('Supplied bank proof hashes differ from its actual candidate overlay')
        prepared_sha256=actual
    return dict(schema='atlas-marine-bank-edge-audit/v1',kind='actual-native-C-source-bank-edges',
        authenticated_bank_pairs=[list(p) for p in sorted(pairs)],unproven_edges=unproven,edges=records,
        prepared_sha256=dict(sorted((prepared_sha256 or {}).items())),
        helper_sha256=compiled.helper_sha256,input_sha256=dict(sorted(inputs.inputs.items())),
        scope_maps=sorted(names),summary=dict(edges=len(records),authenticated_directed_pairs=len(pairs),
            unproven_edges=len(unproven),face_failure_reasons=dict(Counter(f['reason'] for r in records for f in r['face_failures'])),
            halo_failure_reasons=dict(Counter(f['reason'] for r in records for f in r['halo_failures']))),
        actual_helpers_host_compiled=True,RGB555_palette_comparison=True,symbolic_pointer_identity_required=True,
        bytes_only_pointer_equivalence_approved=False,visual_apron_depth=halo_depth,
        whitelist_scope='all-passable-faces-both-cameras-and-all-connections-per-map-pair',
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        native_validated=False,ROM_compiled=False,campaign_validated=False,final_release_validated=False)


def requirement_scope(metadata,requirements):
    names={r['name'] for r in metadata['geometry_plan']['chunks']}
    names.update(requirements.get('transit_maps',[]))
    for key in ('ports','caves','dives','adapters','native_pixels'):
        for row in requirements.get(key,[]):
            for field in ('point','dry','water'):
                if row.get(field):names.add(row[field][0])
            for field in ('surface','interior','depth'):
                if row.get(field):names.add(row[field])
    return names


if __name__=='__main__':
    from prepare_atlas_surf_layout import compose,EVIDENCE
    from atlas_surf_overlay import OverlaySource
    from atlas_surf_layout_requirements import build_requirements
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();layer,metadata=compose(args.source);view=OverlaySource(layer)
    parent=json.loads((EVIDENCE/'parent-inventory.json').read_bytes())
    native=json.loads(gzip.decompress((EVIDENCE/'native-ownership-source.json.gz').read_bytes()))
    requirements=build_requirements(view,metadata,parent,native)
    report=audit_edges(view,scope=requirement_scope(metadata,requirements))
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
