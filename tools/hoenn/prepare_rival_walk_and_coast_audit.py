"""Visible multi-step rival entrances, longer speeches and complete sea rocks."""
import argparse,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_close_vertical_boats import PRIOR,LAYER as PREVIOUS
LAYER='rival-walk-and-coast-audit';PRIOR=PRIOR+[PREVIOUS]

EREN_EXTRA=[
 [('There were Titans all around us.','I reached out... then a flash.'),('I cannot explain that power.','I have to get back to my friends.')],
 [('Armin dreamed of seeing the sea.','He should be here to see this.'),('But MAGMA threatens this world.','I will stop them and find a way.')],
 [('I trusted people who betrayed us.','Now every answer feels like a lie.'),('These POKEMON still trust me.','I have to be worthy of that.')],
 [('I promised to protect my friends.','A wall will not stop me again.'),('If there is a way back home,','I will find it. No matter what.')],
 [('Every day here is another day','I cannot be there to help them.'),('I hear that Titan in my dreams.','I cannot let that fear win!')],
 [('Mikasa... Armin... wait for me!','I am trying to hold it together.'),('My POKEMON are staying with me.','Help me focus before I lose it!')],
]
LUFFY_EXTRA=[
 [('My friends vanished one by one.','I could not even reach them.'),('But they are still my crew!','I am going to bring them back!')],
 [('I remember running at SABAODY.','After that, it is all mixed up.'),('If Nami saw this strange sea,','she would draw us a way home!')],
 [('Sanji would not let us go hungry.','Chopper would take care of us.'),('These POKEMON are my friends too.','I will not leave anyone behind!')],
 [('Usopp would say he knows a way.','Then we would figure it out!'),('Robin always notices things.','Maybe that old ship has a clue.')],
 [('Franky would love all these boats.','Brook would sing until we smiled.'),('Nobody gets to steal our freedom.','Not AQUA. Not anybody!')],
 [('I could not save them at SABAODY.','I am not giving up on them now.'),('You helped me get this far.','Let us get stronger together!')],
]
AFTER_EREN=[
 [('You stayed calm during that fight.','I need to learn how to do that.'),('If you hear about a portal,','tell me. I will keep searching.')],
 [('Armin would have watched each move.','I keep charging in too quickly.'),('Next time I will be stronger.','My friends are counting on me.')],
 [('I know you are trying to help me.','I should not take this out on you.'),('I will follow the next MAGMA trail.','Maybe it will lead to an answer.')],
 [('That battle cleared my head a bit.','My POKEMON fought for me again.'),('I cannot forget who I am fighting','for. Mikasa and Armin need me.')],
 [('I am angry... but you are right.','I cannot fight without thinking.'),('I will keep looking for the truth.','I will not let MAGMA bury it.')],
 [('I can breathe again. Thank you.','You and my POKEMON brought me back.'),('I need answers about this power.','I will face them with you.')],
]
AFTER_LUFFY=[
 [('That was fun! Your POKEMON like you.','I can tell when friends trust you.'),('I will look for my crew some more.','We should battle again!')],
 [('You got me this time!','Now I need food before I go.'),('If you find a clue about SABAODY,','come find me. I will be around!')],
 [('These friends keep getting stronger.','Just like the crew on my ship!'),('I will find everyone somehow.','I know they have not given up.')],
 [('AQUA cannot push us around forever.','The sea belongs to everyone!'),('I am going to check that old ship.','You should come if you find a clue.')],
 [('I wish my crew could meet you.','They would like you too!'),('When I find the way back,','we are going to have a huge meal!')],
 [('That was a great fight, friend!','I am ready to help you now.'),('We will solve this mystery together.','Then I will go back to my crew!')],
]

def strings(pages):
 return ''.join('\t.string "'+line+('\\n' if j==0 else '\\p' if i<len(pages)-1 else '$')+'"\n' for i,page in enumerate(pages) for j,line in enumerate(page))

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ld=json.loads((s/'data/layouts/layouts.json').read_text());ls={l['id']:l for l in ld['layouts']};blocks={};changes=[]
 def load(name):
  m=json.loads((s/f'data/maps/{name}/map.json').read_text());l=ls[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:blocks[p]=list(struct.unpack('<'+'H'*l['width']*l['height'],(s/p).read_bytes()))
  return l,blocks[p]
 for name in ['JourneyWorldFill30Right','JourneyWorldFill31Right']:
  l,v=load(name);w=l['width']
  for y in range(l['height']):
   assert [v[y*w+21]&1023,v[y*w+22]&1023]==([0x111,0x110] if y%2==0 else [0x119,0x118])
   v[y*w+21],v[y*w+22]=([0x510,0x511] if y%2==0 else [0x518,0x519])
  changes.append(dict(map=name,complete_rock_pairs=l['height']//2,collision_preserved=True))
 l,v=load('JourneyWorldSea03')
 for y in [0,1]:
  assert v[y*l['width']+41]&1023==[0x111,0x119][y]
  v[y*l['width']+41]=0x112B
 changes.append(dict(map='JourneyWorldSea03',partial_rock_tiles_removed=2))
 l,v=load('JourneyOneIslandChannel');w=l['width'];shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E]
 land={(i%w,i//w) for i,t in enumerate(v) if t&1023 in shore+[1]};grass=sum(t&1023==1 for t in v)
 for x,y in land:
  row=0 if (x,y-1) not in land else 2 if (x,y+1) not in land else 1
  col=0 if (x-1,y) not in land else 2 if (x+1,y) not in land else 1
  v[y*w+x]=0x3000|shore[row*3+col]
 changes.append(dict(map='JourneyOneIslandChannel',grass_removed=grass))
 for p,v in blocks.items():layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 # Keep all intervening cells clear, including elevation and other NPCs.
 p='src/journey_crossover.c';t=(s/p).read_text();a=t.index('        for (u32 d=0;');b=t.index('\n    return FALSE;',a)
 t=t[:a]+'''        for (u32 distance=4;distance>=2;distance--)
        for (u32 d=0;d<ARRAY_COUNT(directions);d++)
        {
            bool8 clear=TRUE;
            s16 xx=x+distance*directions[d][0],yy=y+distance*directions[d][1];
            for(u32 step=1;step<=distance;step++)
            {
                s16 tx=x+step*directions[d][0],ty=y+step*directions[d][1];
                if(tx<MAP_OFFSET || ty<MAP_OFFSET || tx>=gMapHeader.mapLayout->width+MAP_OFFSET || ty>=gMapHeader.mapLayout->height+MAP_OFFSET
                    || MapGridGetCollisionAt(tx,ty)
                    || MapGridGetElevationAt(tx,ty)!=MapGridGetElevationAt(x,y)
                    || GetObjectEventIdByXY(tx,ty)!=OBJECT_EVENTS_COUNT) {clear=FALSE;break;}
            }
            if(!clear)continue;
            u8 id=SpawnSpecialObjectEventParameterized(entry->gfx,MOVEMENT_TYPE_FACE_DOWN,JOURNEY_RIVAL_LOCALID,xx,yy,MapGridGetElevationAt(xx,yy));
            if(id>=OBJECT_EVENTS_COUNT)return FALSE;
            sJourneyCrossoverActive=i+1;
            gSpecialVar_0x8006=distance-1;
            gSpecialVar_0x8007=d;
            gSpecialVar_LastTalked=JOURNEY_RIVAL_LOCALID;
            ScriptContext_SetupScript(JourneyCrossover_Encounter);
            return TRUE;
        }
    }'''+t[b:];layer.stage(p,t)
 p='data/scripts/journey_crossover.inc';t=(s/p).read_text()
 for direction in ['Up','Down','Left','Right']:
  needle='\tapplymovement 240, JourneyCrossover_Walk'+direction
  replacement=('\tgoto_if_eq VAR_0x8006, 3, JourneyCrossover_Approach'+direction+'3\n'
               '\tgoto_if_eq VAR_0x8006, 2, JourneyCrossover_Approach'+direction+'2\n'+needle)
  assert t.count(needle)==1;t=t.replace(needle,replacement)
  for count in [2,3]:
   t+='\nJourneyCrossover_Approach'+direction+str(count)+'::\n\tapplymovement 240, JourneyCrossover_Walk'+direction+str(count)+'\n\tgoto JourneyCrossover_StartBattle\n'
   t+='JourneyCrossover_Walk'+direction+str(count)+'::\n'+('\twalk_'+direction.lower()+'\n')*count+'\tstep_end\n'
 # Append two pages before the invitation in each existing introduction.
 for hero,extras,after in [('EREN',EREN_EXTRA,AFTER_EREN),('LUFFY',LUFFY_EXTRA,AFTER_LUFFY)]:
  for i,pages in enumerate(extras,1):
   key=hero+str(i);pat=r'(JourneyCrossover_Text_'+key+r'::\n)((?:\t.string.*\n)+)';match=re.search(pat,t);body=match[2];rows=body.splitlines(keepends=True)
   invitation=rows[-2:] if '\\n' in rows[-2] else rows[-1:];cut=len(rows)-len(invitation)
   extension=strings(pages).replace('$','\\p')
   t=t[:match.start(2)]+''.join(rows[:cut])+extension+''.join(invitation)+t[match.end(2):]
   t+='\nJourneyCrossover_Text_After'+key+'::\n'+strings(after[i-1])
 # The visit is recorded only after the matching post-battle speech.
 needle='JourneyCrossover_AfterBattle::\n\tmsgbox JourneyCrossover_Text_After\n\tclosemessage'
 assert needle in t
 dispatch='JourneyCrossover_AfterBattle::\n\tspecial JourneyCrossoverInfo\n'+''.join('\tgoto_if_eq VAR_RESULT, '+str(i)+', JourneyCrossover_After'+key+'\n' for i,key in enumerate([h+str(i) for h in ['EREN','LUFFY'] for i in range(1,7)]))+'\tmsgbox JourneyCrossover_Text_After\n\tgoto JourneyCrossover_Finish\nJourneyCrossover_Finish::\n\tclosemessage'
 t=t.replace(needle,dispatch)
 for key in [h+str(i) for h in ['EREN','LUFFY'] for i in range(1,7)]:t+='\nJourneyCrossover_After'+key+'::\n\tmsgbox JourneyCrossover_Text_After'+key+'\n\tgoto JourneyCrossover_Finish\n'
 layer.stage(p,t)
 return layer.finish(coastal_repairs=changes,rival_max_spawn_distance=4,rival_walk_steps=[1,2,3],clear_path_and_elevation_required=True,longer_introductions=12,individual_postbattle_speeches=12,approved_ports_preserved=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
