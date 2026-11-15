"""Keep the real cyan player visible at valid atlas edges and under the cursor.

This changes only window drawing. It never changes player/world coordinates,
geography, cursor selection, or the four immutable artwork arrays.
"""
import hashlib
from badge_story_layer import read


HELPER=r'''static void JourneyAtlasDrawPlayerMarker(s16 x, s16 y)
{
    s16 left = x - 1, top = y - 1, right = x + 2, bottom = y + 2;
    if (left < 0) left = 0;
    if (top < 0) top = 0;
    if (right > 224) right = 224;
    if (bottom > 112) bottom = 112;
    if (left < right && top < bottom)
        FillWindowPixelRect(2, PIXEL_FILL(5), left, top, right - left, bottom - top);
}

'''


def stage(layer):
    path='src/journey_world_map.c';text=read(layer,path).decode()
    old='    if(playerX>=1 && playerX<223 && playerY>=1 && playerY<111)FillWindowPixelRect(2,PIXEL_FILL(5),playerX-1,playerY-1,3,3);'
    cursor='    FillWindowPixelRect(2,PIXEL_FILL(2),cursorX,cursorY,1,1);'
    anchor='static void WorldDraw(void)'
    if 'JourneyAtlasDrawPlayerMarker' in text or any(text.count(x)!=1 for x in (old,cursor,anchor)):
        raise ValueError('World marker drawing shape changed; review instead of altering projection')
    updated=text.replace(old,'').replace(cursor,cursor+'\n    JourneyAtlasDrawPlayerMarker(playerX,playerY);')
    updated=updated.replace(anchor,HELPER+anchor)
    layer.stage(path,updated)
    return dict(kind='cyan-player-marker-clipped-window-drawing',
                prepared_sha256=hashlib.sha256(updated.encode()).hexdigest(),
                position_or_cursor_coordinates_changed=False,art_changed=False,
                clipped_canvas=[224,112],player_drawn_after_cursor=True,native_validated=False)
