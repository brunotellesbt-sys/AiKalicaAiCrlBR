"""Eight themed rooms with complete furniture and four mandatory sight checkpoints."""
import json,struct

ROOMS={
 'MORTY':(41,53,'stone staircase'), 'WHITNEY':(43,53,'horseshoe conservatory'),
 'STEVEN':(39,65,'offset metal galleries'), 'BUGSY':(55,57,'stepped woodland nursery'),
 'CANDICE':(47,65,'snow switchbacks'), 'CLAIR':(41,63,'dragon side wing'),
 'KAREN':(51,61,'spiral violet salon'), 'OAK':(51,59,'angular research laboratory'),
}

# Distinct floor plans, not scaled or mirrored copies of a shared S. Each
# checkpoint crosses one straight segment; its entire front remains open.
GEOMETRY={
 'MORTY':dict(leader=[20,3],path=[[20,52],[20,39],[8,39],[8,23],[25,23],[25,9],[20,9],[20,4]],
     crossings=[(14,39,'DOWN'),(8,30,'RIGHT'),(17,23,'UP'),(25,14,'LEFT')]),
 'WHITNEY':dict(leader=[29,32],path=[[21,52],[21,40],[7,40],[7,12],[35,12],[35,39],[29,39],[29,33]],
     crossings=[(14,40,'DOWN'),(7,27,'RIGHT'),(21,12,'UP'),(35,23,'LEFT')]),
 'STEVEN':dict(leader=[19,3],path=[[19,64],[19,52],[8,52],[8,40],[19,40],[19,28],[29,28],[29,16],[19,16],[19,4]],
     crossings=[(14,52,'DOWN'),(8,45,'RIGHT'),(24,28,'UP'),(29,21,'LEFT')]),
 'BUGSY':dict(leader=[43,3],path=[[27,56],[27,43],[9,43],[9,30],[25,30],[25,17],[43,17],[43,4]],
     crossings=[(18,43,'DOWN'),(9,35,'RIGHT'),(25,24,'LEFT'),(35,17,'UP')]),
 'CANDICE':dict(leader=[23,3],path=[[23,64],[23,51],[8,51],[8,37],[37,37],[37,23],[10,23],[10,9],[23,9],[23,4]],
     crossings=[(15,51,'DOWN'),(37,31,'LEFT'),(23,23,'UP'),(10,14,'RIGHT')]),
 'CLAIR':dict(leader=[20,3],path=[[20,62],[20,49],[33,49],[33,23],[20,23],[20,4]],
     crossings=[(20,54,'RIGHT'),(27,49,'DOWN'),(33,35,'LEFT'),(26,23,'UP')]),
 'KAREN':dict(leader=[25,25],path=[[25,60],[25,48],[7,48],[7,10],[43,10],[43,40],[18,40],[18,33],[25,33],[25,26]],
     crossings=[(15,48,'DOWN'),(7,27,'RIGHT'),(25,10,'UP'),(43,27,'LEFT')]),
 'OAK':dict(leader=[11,3],path=[[25,58],[25,46],[39,46],[39,32],[17,32],[17,20],[31,20],[31,10],[11,10],[11,4]],
     crossings=[(32,46,'DOWN'),(39,38,'LEFT'),(17,25,'RIGHT'),(22,10,'UP')]),
}

DIRECTIONS={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}

def plan(key):
    w,h,theme=ROOMS[key];c=w//2;g=GEOMETRY[key];lx,ly=g['leader']
    students=[]
    for x,y,facing in g['crossings']:
        dx,dy=DIRECTIONS[facing]
        students.append(dict(position=[x-3*dx,y-3*dy],facing=facing,sight=6))
    return dict(width=w,height=h,theme=theme,leader=[lx,ly],leader_approach=[lx,ly+1],guide=[c+3,h-3],guide_facing='LEFT',
        entry=[c,h-1],safe=[c,h-3],capture=[lx,ly+3],students=students,
        marked_route=g['path'],distinct_floor_plan=key)

def corridors(p):
    w,h=p['width'],p['height'];c=w//2;cells=set()
    def rect(x0,y0,x1,y1):cells.update((x,y) for y in range(y0,y1+1) for x in range(x0,x1+1))
    lx,ly=p['leader'];rect(lx-8,ly,lx+8,ly+4)
    rect(c-8,h-7,c+7,h-2)            # Guide and complete entrance displays.
    for (ax,ay),(bx,by) in zip(p['marked_route'],p['marked_route'][1:]):
        assert ax==bx or ay==by
        rect(min(ax,bx)-1,min(ay,by)-1,max(ax,bx)+1,max(ay,by)+1)
    # Each sightline spans a seven-by-five open room, not a narrow niche.
    for t in p['students']:
        x,y=t['position'];dx,dy=DIRECTIONS[t['facing']]
        cells.update((x+dx*d+dy*side,y+dy*d+dx*side) for d in range(7) for side in range(-2,3))
    return {(x,y) for x,y in cells if 0<x<w-1 and 2<=y<h}

def build(renderer,bank,key):
    p=plan(key);w,h=p['width'],p['height'];c=w//2;lx,ly=p['leader'];display=c-7
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
      'CANDICE':('FallarborTown',0x279,'snow'),'CLAIR':(lance,0x310,'slate'),
      'KAREN':(dark,0x2f0,None),'OAK':(lab,0x281,None)}
    fm,ft,fx=floors[key]
    floor=(fm,ft,0x3000,0,fx);grid=[floor]*(w*h)
    def put(x,y,n,mid,blocked=False,effect=None,behavior=0):
        assert 0<=x<w and 0<=y<h
        grid[y*w+x]=(n,mid,0x3400 if blocked else 0x3000,behavior,effect)
    def stamp(n,sx,sy,ww,hh,x,y,effect=None):
        assert 1<=x and x+ww<w and 2<=y and y+hh<=h-1
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
    for y in range(3 if key in ['STEVEN','CLAIR'] else 2,h-1):
        for x in range(1,w-1):
            if (x,y) not in route:
                edge=(x,y-1) in route or (x,y+1) in route
                put(x,y,wall,cap if edge else body,True,effect if edge else 'wallfill_'+key)
    # Complete furniture stays in the spacious leader chamber and side bays.
    if key=='MORTY':
        for x in [lx-5,lx-4,lx+3,lx+4]:
            put(x,ly+1,tower,0x291,True,'stone')
        for x in [display,display+1,display+4]:put(x,h-5,tower,0x291,True,'stone')
    elif key=='WHITNEY':
        for x in [lx-5,lx-4,lx+3,lx+4]:
            put(x,ly+2,flower,0x2b6,True)
        for x in [lx-5,lx+3]:
            for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(x+dx,ly+dy,flower,mid,True)
        for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(display+dx,h-6+dy,flower,mid,True)
        for x in [display+4,display+5]:put(x,h-5,flower,0x2b6,True)
    elif key=='STEVEN':
        for x in [lx-5,lx+3]:
            stamp(space,10,4,2,2,x,ly+1)
        stamp(space,10,4,2,2,display,h-6)
    elif key=='BUGSY':
        for x in [lx-5,lx-4,lx+3,lx+4]:
            put(x,ly+2,flower,0x2b6,True)
        for x in [lx-5,lx+3]:
            for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(x+dx,ly+dy,flower,mid,True)
        for x in [display,display+4]:
            for dx,dy,mid in [(0,0,0x28d),(1,0,0x28e),(0,1,0x295),(1,1,0x296)]:put(x+dx,h-6+dy,flower,mid,True)
    elif key=='CANDICE':
        for x in [lx-5,lx+4]:
            for y in [ly+1,ly+2]:put(x,y,ice,0x37d,True)
        for x,y in [(display,h-6),(display+1,h-6),(display+4,h-5)]:put(x,y,ice,0x37d,True)
    elif key=='CLAIR':
        # Use the complete long sculpture from Lance's dragon chamber,
        # including its curved body and pedestal (not the generic gym statue).
        for x,y in [(lx-5,ly),(lx+3,ly),(display,h-6),(c+5,h-6)]:
            stamp(lance,2,10,2,3,x,y,'slate')
        for dy in range(3):
            for dx in range(3):put(c-1+dx,dy,drake,native(drake,5+dx,dy),True)
    elif key=='KAREN':
        for x in [lx-5,lx+4]:
            stamp(dark,2,2,1,3,x,ly)
        for x in [display,display+5]:stamp(dark,2,2,1,3,x,h-6)
    else:
        for x in [lx-6,lx+4]:stamp(lab,0,0,3,3,x,ly)
        stamp(lab,9,0,4,3,display,h-6)
    # A continuous, simple trail makes each crossing readable. It uses the
    # room's own palette and ordinary walking behavior, never a puzzle tile.
    trail=set()
    for (ax,ay),(bx,by) in zip(p['marked_route'],p['marked_route'][1:]):
        assert ax==bx or ay==by
        for yy in range(min(ay,by),max(ay,by)+1):
            for xx in range(min(ax,bx),max(ax,bx)+1):
                if yy<h-1:assert (xx,yy) in route and not grid[yy*w+xx][2]&0xc00,(key,'decoration cuts path',xx,yy)
                for side in [0,1]:
                    x,y=(xx+side,yy) if ax==bx else (xx,yy+side)
                    if (x,y) in route and not grid[y*w+x][2]&0xc00:
                        put(x,y,fm,ft,False,'carpet' if key=='CLAIR' else 'trail_'+(fx or 'plain'));trail.add((x,y))
    for x,y in p['marked_route'][:-1]:
        if y<h-1:assert (x,y) in trail,(key,'decoration cuts marked route',x,y)
    # Every trainer looks across the visible path toward an actual crossing.
    for t in p['students']:
        x,y=t['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[t['facing']]
        assert any((x+dx*d,y+dy*d) in trail for d in range(1,7)),(key,'trainer faces away from marked route')
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
    p['guide_near_entrance']=True;p['thematic_entrance_display']=True;p['dragon_statues']=4 if key=='CLAIR' else 0
    return values,p
