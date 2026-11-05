"""Source aliases and native whole-frame layouts must not erase static actors."""
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from PIL import Image

from render_sea_maps import MapRenderer


class NativeSpriteRenderer(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='native-sprite-review-')
        self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)
        def write(name,text):
            path=self.source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        self.write=write
        write('data/layouts/layouts.json',json.dumps(dict(layouts=[])))
        write('src/data/tilesets/headers.h','')
        write('src/data/tilesets/metatiles.h','')
        write('include/constants/event_objects.h','#define OBJ_EVENT_GFX_CASE_ALIAS OBJ_EVENT_GFX_JOURNEY_FAMILY_CASE\n')
        write('src/data/object_events/object_event_graphics_info_pointers.h','''
const struct ObjectEventGraphicsInfo *const pointers[] = {
 [OBJ_EVENT_GFX_JOURNEY_FAMILY_CASE] = &gObjectEventGraphicsInfo_JourneyFamilyCase,
 [OBJ_EVENT_GFX_REORDERED] = &gObjectEventGraphicsInfo_Reordered,
};
''')
        write('src/data/object_events/object_event_graphics_info.h','''
const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyFamilyCase = {
 .size=128, .width=16, .height=16, .paletteTag=OBJ_EVENT_PAL_TAG_NPC_3,
 .oam=&gObjectEventBaseOam_16x16, .images=sPicTable_JourneyFamilyCase,
};
const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Reordered = {
 .size=128, .width=16, .height=16, .paletteTag=OBJ_EVENT_PAL_TAG_NPC_3,
 .oam=&gObjectEventBaseOam_16x16, .images=sPicTable_Reordered,
};
''')
        write('src/data/object_events/object_event_pic_tables.h','''
static const struct SpriteFrameImage sPicTable_JourneyFamilyCase[] = {
 overworld_frame(gObjectEventPic_JourneyFamilyCase,2,2,0),
};
static const struct SpriteFrameImage sPicTable_Reordered[] = {
 overworld_frame(gObjectEventPic_Reordered,2,2,3),
 overworld_frame(gObjectEventPic_Reordered,2,2,1),
};
''')
        words=struct.unpack('<64H',bytes(32)+b'\x11'*32+b'\x22'*32+b'\x33'*32)
        write('src/data/object_events/object_event_graphics.h','''
const u16 gObjectEventPic_JourneyFamilyCase[] = {'''+','.join(hex(v) for v in words)+'''};
const u32 gObjectEventPic_Reordered[] = INCBIN_U32("graphics/reordered.4bpp");
const u16 gObjectEventPal_Npc3[] = INCBIN_U16("graphics/npc_3.gbapal");
''')
        write('src/event_object_movement.c','{gObjectEventPal_Npc3, OBJ_EVENT_PAL_TAG_NPC_3},\n')
        self.colors=[(112,192,160),(248,208,176),(248,192,144),(216,144,112),(88,112,232)]+[(0,0,0)]*11
        self.palette('graphics/npc_3.pal',self.colors)
        self.sheet('graphics/reordered.png',16,4)
        # Source token pasting and form aliases are expanded by the actual C
        # preprocessor. The incorrect old filename guess cannot find these.
        write('src/pokemon.c','''
#define SIZE_32x32 1
#define SIZE_64x64 0
enum Species {SPECIES_KELDEO_ORDINARY=647,SPECIES_KELDEO=SPECIES_KELDEO_ORDINARY};
#define FORM_INFO(Name,Size) { \\
 .overworldData={.width=(Size==1?32:64),.height=(Size==1?32:64), \\
 .size=(Size==1?512:2048),.oam=(Size==1?&gObjectEventBaseOam_32x32:&gObjectEventBaseOam_64x64), \\
 .images=sPicTable_##Name}, \\
 .overworldPalette=gOverworldPalette_##Name, .overworldShinyPalette=gShinyOverworldPalette_##Name, }
const struct SpeciesInfo gSpeciesInfo[] = {
 [SPECIES_KELDEO_ORDINARY] = FORM_INFO(KeldeoOrdinary,SIZE_32x32),
 [SPECIES_ARCEUS_NORMAL] = FORM_INFO(ArceusNormal,SIZE_64x64),
};
''')
        write('src/data/object_events/object_event_pic_tables_followers.h','''
static const struct SpriteFrameImage sPicTable_KeldeoOrdinary[] = {overworld_ascending_frames(gObjectEventPic_KeldeoOrdinary,4,4)};
static const struct SpriteFrameImage sPicTable_ArceusNormal[] = {overworld_ascending_frames(gObjectEventPic_ArceusNormal,8,8)};
''')
        text=''
        for token,folder,size in [('KeldeoOrdinary','keldeo',32),('ArceusNormal','arceus',64)]:
            text+=f'''#define gObjectEventPic_{token} gObjectEventPic_Native{token}
const u32 gObjectEventPic_Native{token}[] = INCBIN_COMP("graphics/pokemon/{folder}/overworld.4bpp");
const u16 gOverworldPalette_{token}[] = INCBIN_U16("graphics/pokemon/{folder}/overworld_normal.gbapal");
const u16 gShinyOverworldPalette_{token}[] = INCBIN_U16("graphics/pokemon/{folder}/overworld_shiny.gbapal");
'''
            self.sheet(f'graphics/pokemon/{folder}/overworld.png',size,2)
            self.palette(f'graphics/pokemon/{folder}/overworld_normal.pal',self.colors)
            colors=list(self.colors);colors[1]=(8,16,248)
            self.palette(f'graphics/pokemon/{folder}/overworld_shiny.pal',colors)
        write('src/data/graphics/pokemon.h',text)

    def palette(self,name,colors):
        self.write(name,'JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')

    def sheet(self,name,size,frames):
        image=Image.new('P',(size*frames,size),0)
        image.putpalette([0]*768)
        for frame in range(frames):
            image.putpixel((frame*size+1,1),frame+1)
            image.putpixel(((frame+1)*size-1,size-1),3)
        target=self.source/name;target.parent.mkdir(parents=True,exist_ok=True);image.save(target)

    def test_inline_family_case_uses_gba_tile_order_and_index_zero_transparency(self):
        renderer=MapRenderer(self.source);image=renderer.sprite('OBJ_EVENT_GFX_CASE_ALIAS')
        self.assertEqual(image.size,(16,16))
        self.assertEqual(image.getpixel((0,0)),(0,0,0,0))
        for xy,color in [((8,0),self.colors[1]),((0,8),self.colors[2]),((15,15),self.colors[3])]:
            self.assertEqual(image.getpixel(xy),(*color,255))
        self.assertEqual(sum(bool(p[3]) for p in image.getdata()),192)

    def test_native_form_macros_aliases_palettes_and_full_bottom_row(self):
        self.assertIsNotNone(shutil.which('cpp'),'Native C preprocessor is required')
        renderer=MapRenderer(self.source)
        for token,size,folder in [('KELDEO_ORDINARY',32,'keldeo'),('ARCEUS_NORMAL',64,'arceus')]:
            with self.subTest(token=token):
                image=renderer.sprite('OBJ_EVENT_GFX_SPECIES('+token+')')
                self.assertEqual(image.size,(size,size))
                self.assertEqual(image.getpixel((0,0)),(0,0,0,0))
                self.assertEqual(image.getpixel((size-1,size-1)),(*self.colors[3],255))
                descriptor=renderer.sprite_sources['OBJ_EVENT_GFX_SPECIES('+token+')#0']
                self.assertEqual(descriptor['graphic_source'],f'graphics/pokemon/{folder}/overworld.png')
                self.assertEqual(descriptor['oam'],f'&gObjectEventBaseOam_{size}x{size}')
        shiny=renderer.sprite('OBJ_EVENT_GFX_SPECIES_SHINY(KELDEO_ORDINARY)')
        self.assertEqual(shiny.getpixel((1,1)),(8,16,248,255))
        female=renderer.sprite('OBJ_EVENT_GFX_SPECIES_FEMALE(KELDEO_ORDINARY)')
        self.assertEqual(female.tobytes(),renderer.sprite('OBJ_EVENT_GFX_SPECIES(KELDEO_ORDINARY)').tobytes())
        self.assertEqual(renderer.sprite('OBJ_EVENT_GFX_SPECIES(KELDEO)').tobytes(),renderer.sprite('OBJ_EVENT_GFX_SPECIES(KELDEO_ORDINARY)').tobytes())

    def test_explicit_native_frame_table_order_and_bounds(self):
        renderer=MapRenderer(self.source)
        self.assertEqual(renderer.sprite('OBJ_EVENT_GFX_REORDERED',0).getpixel((1,1)),(*self.colors[4],255))
        self.assertEqual(renderer.sprite('OBJ_EVENT_GFX_REORDERED',1).getpixel((1,1)),(*self.colors[2],255))
        with self.assertRaises(AssertionError):renderer.sprite('OBJ_EVENT_GFX_REORDERED',2)
        with self.assertRaises(AssertionError):renderer.sprite('OBJ_EVENT_GFX_REORDERED',-1)

    def test_indexed_export_with_256_colors_uses_native_first_palette_bank(self):
        (self.source/'graphics/npc_3.pal').unlink()
        colors=[(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in self.colors]
        raw=struct.pack('<256H',*(colors+[0x7C1F]*240))
        (self.source/'graphics/npc_3.gbapal').write_bytes(raw)
        image=MapRenderer(self.source).sprite('OBJ_EVENT_GFX_CASE_ALIAS')
        self.assertEqual(image.getpixel((8,0)),(*self.colors[1],255))
        self.assertEqual(image.getpixel((15,15)),(*self.colors[3],255))
        (self.source/'graphics/npc_3.gbapal').write_bytes(raw[:30])
        with self.assertRaises(AssertionError):MapRenderer(self.source).sprite('OBJ_EVENT_GFX_CASE_ALIAS')

    def test_relative_frame_bounds_reject_partial_or_missing_frames(self):
        self.assertIsNotNone(shutil.which('cpp'),'Native C preprocessor is required')
        renderer=MapRenderer(self.source)
        self.assertEqual(renderer.sprite('OBJ_EVENT_GFX_SPECIES(KELDEO_ORDINARY)',1).getpixel((1,1)),(*self.colors[2],255))
        with self.assertRaises(AssertionError):renderer.sprite('OBJ_EVENT_GFX_SPECIES(KELDEO_ORDINARY)',2)
        self.sheet('graphics/pokemon/keldeo/overworld.png',31,2)
        with self.assertRaises(AssertionError):MapRenderer(self.source).sprite('OBJ_EVENT_GFX_SPECIES(KELDEO_ORDINARY)')


if __name__=='__main__':unittest.main()
