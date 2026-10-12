"""Add optional exact 2x zoom to menu/wall/Fly maps and Pokédex habitats."""
import argparse,hashlib,json
from pathlib import Path
from prepare_mega_origin_reversion import PRIOR,LAYER as PREVIOUS
ROOT=Path(__file__).resolve().parents[2];LAYER='sharp-world-map';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None;assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 stage('include/journey_atlas_zoom.inc',(ROOT/'tools/hoenn/world_map_zoom.c.inc').read_text())
 p='src/journey_world_map.c';t=(source/p).read_text().replace('#include "data/journey_world_position.h"','#include "data/journey_world_position.h"\n#include "journey_atlas_zoom.inc"')
 needle='    u8 x, y, state, fly, playerX, playerY;';assert needle in t;t=t.replace(needle,needle+'\n    u8 zoom,viewX,viewY;\n    u8 *zoomTiles;')
 needle='    FillWindowPixelBuffer(2,PIXEL_FILL(0));';assert t.count(needle)==1
 t=t.replace(needle,'''    JourneyAtlasDraw(1,sJourneyWorldMap->tilemap,0,sJourneyWorldMap->zoom,sJourneyWorldMap->x,sJourneyWorldMap->y,sJourneyWorldMap->zoomTiles,&sJourneyWorldMap->viewX,&sJourneyWorldMap->viewY);
    s16 playerX=sJourneyWorldMap->zoom?2*((s16)sJourneyWorldMap->playerX-sJourneyWorldMap->viewX):sJourneyWorldMap->playerX;
    s16 playerY=sJourneyWorldMap->zoom?2*((s16)sJourneyWorldMap->playerY-sJourneyWorldMap->viewY):sJourneyWorldMap->playerY;
    s16 cursorX=sJourneyWorldMap->zoom?2*((s16)sJourneyWorldMap->x-sJourneyWorldMap->viewX):sJourneyWorldMap->x;
    s16 cursorY=sJourneyWorldMap->zoom?2*((s16)sJourneyWorldMap->y-sJourneyWorldMap->viewY):sJourneyWorldMap->y;
'''+needle)
 t=t.replace('    FillWindowPixelRect(2,PIXEL_FILL(5),sJourneyWorldMap->playerX-1,sJourneyWorldMap->playerY-1,3,3);','    if(playerX>=1 && playerX<223 && playerY>=1 && playerY<111)FillWindowPixelRect(2,PIXEL_FILL(5),playerX-1,playerY-1,3,3);')
 t=t.replace('sJourneyWorldMap->x-3,sJourneyWorldMap->y-3','cursorX-3,cursorY-3').replace('sJourneyWorldMap->x-2,sJourneyWorldMap->y-2','cursorX-2,cursorY-2').replace('sJourneyWorldMap->x,sJourneyWorldMap->y,1,1','cursorX,cursorY,1,1')
 t=t.replace('A: FLY  SELECT: YOU  B: BACK','A: FLY  R: ZOOM  B: BACK').replace('D-PAD: MOVE  SELECT: YOU  B: BACK','R: ZOOM  SELECT: YOU  B: BACK')
 needle='        else if(sJourneyWorldMap->fly && JOY_NEW(A_BUTTON)) {';assert needle in t
 t=t.replace(needle,'''        else if(JOY_NEW(R_BUTTON) || (!sJourneyWorldMap->fly && JOY_NEW(A_BUTTON))) {
            if(sJourneyWorldMap->zoomTiles==NULL)sJourneyWorldMap->zoomTiles=AllocZeroed(393*32);
            if(sJourneyWorldMap->zoomTiles!=NULL){sJourneyWorldMap->zoom^=1;WorldDraw();}
            else PlaySE(SE_FAILURE);
        }
'''+needle)
 needle='        FREE_AND_SET_NULL(sJourneyWorldMap);';assert needle in t;t=t.replace(needle,'        TRY_FREE_AND_SET_NULL(sJourneyWorldMap->zoomTiles);\n'+needle);stage(p,t)
 p='src/journey_world_dex.c';t=(source/p).read_text().replace('#include "data/journey_world_map.h"','#include "data/journey_world_map.h"\n#include "journey_atlas_zoom.inc"');needle='    u8 sprites[32], count, caption;';assert needle in t;t=t.replace(needle,needle+'\n    u8 zoom,focus,left,top;\n    u8 *zoomTiles;')
 t=t.replace('sprite->invisible = (++sprite->data[0] % 48) >= 36;','sprite->invisible = sprite->data[1] || (++sprite->data[0] % 48) >= 36;')
 needle='static void Task_WorldDex(u8 id)';assert needle in t
 helper='''static void WorldDexZoom(void)
{
    u8 x=112,y=56;
    if(sWorldDex->count){struct Sprite *focus=&gSprites[sWorldDex->sprites[sWorldDex->focus]];x=focus->data[2];y=focus->data[3];}
    JourneyAtlasDraw(3,GetBgTilemapBuffer(3),7,sWorldDex->zoom,x,y,sWorldDex->zoomTiles,&sWorldDex->left,&sWorldDex->top);
    for(u32 i=0;i<sWorldDex->count;i++)
    {
        struct Sprite *sprite=&gSprites[sWorldDex->sprites[i]];
        s16 px=sWorldDex->zoom?2*(sprite->data[2]-sWorldDex->left):sprite->data[2];
        s16 py=sWorldDex->zoom?2*(sprite->data[3]-sWorldDex->top):sprite->data[3];
        sprite->x=px+8;sprite->y=py+24;sprite->data[1]=px<0 || px>=224 || py<0 || py>=112;
    }
    if(sWorldDex->caption!=WINDOW_NONE)PutWindowTilemap(sWorldDex->caption);
    CopyBgTilemapBufferToVram(3);
}
'''
 t=t.replace(needle,helper+'\n'+needle)
 needle='                if(sprite!=MAX_SPRITES)sWorldDex->sprites[sWorldDex->count++]=sprite;';assert needle in t;t=t.replace(needle,'                if(sprite!=MAX_SPRITES){sWorldDex->sprites[sWorldDex->count++]=sprite;gSprites[sprite].data[2]=sWorldDexLocations[i].x;gSprites[sprite].data[3]=sWorldDexLocations[i].y;}')
 needle='        if(JOY_NEW(B_BUTTON) || JOY_NEW(DPAD_LEFT) || JOY_NEW(L_BUTTON))result=1;';assert needle in t;t=t.replace(needle,'''        if(JOY_NEW(A_BUTTON))
        {
            if(sWorldDex->zoomTiles==NULL)sWorldDex->zoomTiles=AllocZeroed(393*32);
            if(sWorldDex->zoomTiles!=NULL){sWorldDex->zoom^=1;WorldDexZoom();}
            else PlaySE(SE_FAILURE);
            return;
        }
        if(sWorldDex->zoom && sWorldDex->count && (JOY_NEW(DPAD_UP) || JOY_NEW(DPAD_DOWN)))
        {sWorldDex->focus=(sWorldDex->focus+1)%sWorldDex->count;WorldDexZoom();return;}
'''+needle)
 t=t.replace('ORANGE MARKS: LOCATIONS','A: ZOOM  ORANGE: LOCATIONS');needle='    *sWorldDex->result=gTasks[id].data[1];FREE_AND_SET_NULL(sWorldDex);DestroyTask(id);';assert needle in t;t=t.replace(needle,'    TRY_FREE_AND_SET_NULL(sWorldDex->zoomTiles);\n'+needle);stage(p,t)
 r=dict(layer=LAYER,zoom_factor=2,nearest_neighbor_only=True,full_map_geography_unchanged=True,menu_and_pokemon_center_wall_and_fly_supported=True,pokedex_habitat_zoom=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
