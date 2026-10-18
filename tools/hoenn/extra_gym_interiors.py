"""Eight themed rooms with complete furniture and four mandatory sight checkpoints."""
import json,struct

ROOMS={
 'MORTY':(25,34,'stone hall'), 'WHITNEY':(27,31,'conservatory'),
 'STEVEN':(28,35,'metal gallery'), 'BUGSY':(25,33,'woodland nursery'),
 'CANDICE':(25,35,'snow room'), 'CLAIR':(27,37,'dragon shrine'),
 'KAREN':(29,33,'violet salon'), 'OAK':(31,36,'research laboratory'),
}

def plan(key):
    w,h,theme=ROOMS[key];c=w//2
    students=[dict(position=[c-2,h-10],facing='DOWN',sight=6),dict(position=[1,h-12],facing='RIGHT',sight=6),
              dict(position=[w-8,h-10],facing='UP',sight=6),dict(position=[w-2,9],facing='LEFT',sight=6)]
    return dict(width=w,height=h,theme=theme,leader=[c,3],leader_approach=[c,4],guide=[1,3],
        entry=[c,h-1],safe=[c,h-3],capture=[c,6],students=students)

def corridors(p):
    w,h=p['width'],p['height'];c=w//2;cells=set()
    def rect(x0,y0,x1,y1):cells.update((x,y) for y in range(y0,y1+1) for x in range(x0,x1+1))
    rect(1,3,w-2,6)                  # Leader chamber, reached at the end.
    rect(w-6,5,w-3,h-14)             # Fourth checkpoint: upper east hall.
    rect(3,h-16,w-5,h-12)            # Third checkpoint: central gallery.
    rect(2,h-14,5,h-6)               # Second checkpoint: western hall.
    rect(1,h-7,c+1,h-4)              # First checkpoint: lower gallery.
    rect(c,h-5,c+1,h-2)
    rect(c-1,h-3,c+1,h-2)            # Empty arrival area.
    # Broad open rooms replace the former one-tile trainer recesses. Each
    # actor stands at a room edge, with a three-tile-wide clear approach and
    # room to either side. The mandatory crossing is ahead of the actor;
    # no partition or furniture is placed between trainer and player.
    rect(c-4,h-10,c,h-4)
    rect(1,h-14,7,h-10)
    rect(w-10,h-16,w-6,h-10)
    rect(w-8,7,w-2,11)
    for t in p['students']:
        x,y=t['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[t['facing']]
        cells.update((x+dx*d,y+dy*d) for d in range(t['sight']+1))
    return cells

def build(renderer,bank,key):
    p=plan(key);w,h=p['width'],p['height'];c=w//2
    tower='PokemonTower_3F_Frlg';flower='CeladonCity_Gym_Frlg';space='MossdeepCity_SpaceCenter_1F'
    lab='PalletTown_ProfessorOaksLab_Frlg';lance='PokemonLeague_LancesRoom_Frlg';drake='EverGrandeCity_DrakesRoom';dark='PokemonLeague_AgathasRoom_Frlg';ice='ShoalCave_LowTideIceRoom'
    cache={}
    def native(n,x,y):
        if n not in cache:
            m=json.loads((renderer.source/f'data/maps/{n}/map.json').read_text());l=renderer.layouts[m['layout']]
            cache[n]=(l,list(struct.unpack('<'+'H'*(l['width']*l['height']),(renderer.source/l['blockdata_filepath']).read_bytes())))
        l,v=cache[n];return v[y*l['width']+x]&1023
    floors={
      'MORTY':(tower,0x282,'stone'), 'WHITNEY':(flower,0x2a5,None),
      'STEVEN':(space,native(space,4,3),None),'BUGSY':('FallarborTown',0x279,None),
      'CANDICE':('FallarborTown',0x279,'snow'),'CLAIR':(lance,0x2f0,'slate'),
      'KAREN':(dark,0x2f0,None),'OAK':(lab,0x281,None)}
    fm,ft,fx=floors[key]
    floor=(fm,ft,0x3000,0,fx);grid=[floor]*(w*h)
    def put(x,y,n,mid,blocked=False,effect=None,behavior=0):
        assert 0<=x<w and 0<=y<h
        grid[y*w+x]=(n,mid,0x3400 if blocked else 0x3000,behavior,effect)
    def stamp(n,sx,sy,ww,hh,x,y,effect=None):
        assert 1<=x and x+ww<w and 2<=y and y+hh<h-1
        for dy in range(hh):
            for dx in range(ww):put(x+dx,y+dy,n,native(n,sx+dx,sy+dy),True,effect)
    # Each material has its own complete north wall, side edging and foot.
    for x in range(w):
        if key=='MORTY':
            for y,mid in enumerate([0x298,0x2a0]):put(x,y,tower,mid,True)
            put(x,h-1,tower,0x298,True)
        elif key=='WHITNEY':
            for y in range(2):put(x,y,flower,0x283 if y==0 else 0x28b,True)
            put(x,h-1,flower,0x2a0,True)
        elif key=='STEVEN':
            for y,mid in enumerate([0x2f8,0x300,0x366]):put(x,y,space,mid,True)
            put(x,h-1,space,0x219,True)
        elif key in ['BUGSY','OAK']:
            effect='wood' if key=='BUGSY' else 'lab'
            for y,mid in enumerate([0x69,0x71]):put(x,y,lab,mid,True,effect)
            put(x,h-1,lab,0x69,True,effect)
        elif key=='CANDICE':
            for y in range(2):put(x,y,ice,native(ice,3+x%2,y),True)
            put(x,h-1,ice,native(ice,3+x%2,0),True)
        elif key=='CLAIR':
            for y in range(3):put(x,y,drake,native(drake,2+x%2,y),True)
            put(x,h-1,drake,0x208,True)
        else:
            for y in range(2):put(x,y,dark,native(dark,3+x%2,y),True,'violet')
            put(x,h-1,dark,native(dark,3+x%2,0),True,'violet')
    for y in range(2,h-1):
        if key=='MORTY':left,right=(tower,0x28b,None),(tower,0x28a,None)
        elif key=='WHITNEY':left=right=(flower,0x2a0,None)
        elif key=='STEVEN':left=right=(space,0x366,None)
        elif key=='CANDICE':left,right=(ice,native(ice,0,4+y%2),None),(ice,native(ice,19,4+y%2),None)
        elif key=='CLAIR':left=right=(drake,0x204,None)
        elif key=='KAREN':left=right=(dark,native(dark,3,1),'violet')
        else:left=right=(lab,0x69,'wood' if key=='BUGSY' else 'lab')
        for x,spec in [(0,left),(w-1,right)]:put(x,y,spec[0],spec[1],True,spec[2])
    # Solid themed partitions close every bypass. Their caps and body use
    # native wall materials, while broad galleries allow passing a defeated
    # trainer. No switches, doors, sliding floors or other puzzle mechanics.
    route=corridors(p)
    materials={'MORTY':(tower,0x298,0x2a0,None),'WHITNEY':(flower,0x283,0x28b,None),
        'STEVEN':(space,0x2f8,0x300,None),'BUGSY':(lab,0x69,0x71,'wood'),
        'CANDICE':(ice,native(ice,3,0),native(ice,3,1),None),
        'CLAIR':(drake,0x204,0x208,None),'KAREN':(dark,native(dark,3,0),native(dark,3,1),'violet'),
        'OAK':(lab,0x69,0x71,'lab')}
    wall,cap,body,effect=materials[key]
    for y in range(3,h-1):
        for x in range(1,w-1):
            if (x,y) not in route:
                edge=(x,y-1) in route or (x,y+1) in route
                put(x,y,wall,cap if edge else body,True,effect if edge else 'wallfill_'+key)
    # Complete furniture stays in the spacious leader chamber and side bays.
    if key=='MORTY':
        for x in [2,3,w-4,w-3]:
            put(x,4,tower,0x291,True,'stone')
    elif key=='WHITNEY':
        for x in [2,3,w-4,w-3]:
            put(x,4,flower,0x2b6,True)
        for x in [2,w-4]:
            for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(x+dx,5+dy,flower,mid,True)
    elif key=='STEVEN':
        for x in [2,w-4]:
            stamp(space,10,4,2,2,x,4)
    elif key=='BUGSY':
        for x in [2,3,w-4,w-3]:
            for y in [4,5]:put(x,y,flower,0x2b6,True)
        for x in [2,w-4]:
            for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(x+dx,5+dy,flower,mid,True)
    elif key=='CANDICE':
        for x in [2,w-3]:
            for y in [4,6]:put(x,y,ice,0x37d,True)
    elif key=='CLAIR':
        for x in [2,w-3]:
            stamp(lance,1,16,1,2,x,4,'slate')
        for y in range(4,h-2):
            for x in range(c-1,c+2):
                if (x,y) in route and not grid[y*w+x][2]&0xc00:put(x,y,lance,0x2f0,False,'carpet')
        for dy in range(3):
            for dx in range(3):put(c-1+dx,dy,drake,native(drake,5+dx,dy),True)
    elif key=='KAREN':
        for x in [2,w-3]:
            stamp(dark,2,2,1,3,x,3)
    else:
        for x in [2,w-5]:stamp(lab,0,0,3,3,x,3)
        stamp(lab,9,0,4,3,1,h-7)
    # Floor underneath actors and every straight approach is always ordinary
    # walking terrain. Snow and all other themes have no sliding or traps.
    for actor in [p['leader'],p['leader_approach'],p['guide'],p['safe']]:
        assert not grid[actor[1]*w+actor[0]][2]&0xc00,(key,'actor intersects prop',actor)
    for student in p['students']:
        x,y=student['position']
        dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
        for distance in range(student['sight']+1):
            xx,yy=x+dx*distance,y+dy*distance
            assert 0<xx<w-1 and 1<yy<h-1
            assert not grid[yy*w+xx][2]&0xc00,(key,'sightline intersects prop',xx,yy)
            assert [xx,yy] not in [other['position'] for other in p['students'] if other is not student],(key,'trainer blocks sightline')
            for side in [-1,1]:
                sx,sy=xx+dy*side,yy+dx*side
                assert not grid[sy*w+sx][2]&0xc00,(key,'trainer approach narrows into a niche',sx,sy)
    # A two-tile native floor exit; there are no interior doors or puzzles.
    for dx in range(2):
        mid=native('RustboroCity_Gym',5+dx,19)
        grid[(h-1)*w+c+dx]=('RustboroCity_Gym',mid,0x3000,None,None)
    values=[upper|bank.add(n,mid,behavior,effect) for n,mid,upper,behavior,effect in grid]
    p['no_puzzles']=True;p['complete_native_props']=True;p['ordinary_walking_floor']=True
    return values,p
