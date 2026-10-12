// Shared edge anchors make adjoining maps agree at the connection itself.
// Distances use local tile coordinates, so short moves never select a distant
// route centre merely because the map ID changed.
u16 JourneyWorldMapPosition(void)
{
    u16 point = JourneyWorldMapPlayerPoint();
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    s16 x, y;
    u32 sx = 0, sy = 0, total = 0, weight, distance;
    s32 dx, dy;
    u16 i;
    const struct JourneyWorldProjection *p = NULL;
    PlayerGetDestCoords(&x, &y);
    x -= MAP_OFFSET; y -= MAP_OFFSET;
    for (i = 0; i < ARRAY_COUNT(sWorldProjections); i++)
        if (sWorldProjections[i].map == map) { p = &sWorldProjections[i]; break; }
    if (p == NULL)
        return sWorldPoints[point].x | (sWorldPoints[point].y << 8);
    for (i = 0; i < p->count + 1; i++)
    {
        const struct JourneyWorldAnchor *a = &sWorldAnchors[p->first + i];
        dx = x < a->left ? a->left - x : x > a->right ? x - a->right : 0;
        dy = y < a->top ? a->top - y : y > a->bottom ? y - a->bottom : 0;
        distance = dx * dx + dy * dy;
        if (distance == 0) return a->x | (a->y << 8);
        weight = 1048576 / distance;
        sx += weight * a->x; sy += weight * a->y; total += weight;
    }
    if (total == 0) return sWorldPoints[point].x | (sWorldPoints[point].y << 8);
    return ((sx + total / 2) / total) | (((sy + total / 2) / total) << 8);
}
