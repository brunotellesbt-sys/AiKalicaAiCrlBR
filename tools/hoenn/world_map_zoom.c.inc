// Exact nearest-neighbor 2x sampling; no smoothing or invented geography.
static void JourneyAtlasDraw(u8 bg,u16 *tilemap,u8 palette,bool8 zoom,u8 centreX,u8 centreY,u8 *tiles,u8 *left,u8 *top)
{
    u32 i,x,y;
    if(!zoom)
    {
        *left=*top=0;
        for(i=0;i<1024;i++)tilemap[i]=sWorldTilemap[i]|(palette<<12);
        LoadBgTiles(bg,sWorldTiles,sizeof(sWorldTiles),0);
    }
    else
    {
        *left=centreX>56?min(112,centreX-56):0;
        *top=centreY>28?min(56,centreY-28):0;
        for(i=0;i<393*32;i++)tiles[i]=0;
        for(i=0;i<1024;i++)tilemap[i]=palette<<12;
        for(y=0;y<112;y++)for(x=0;x<224;x++)
        {
            u32 sx=*left+x/2,sy=*top+y/2;
            u32 tile=sWorldTilemap[(sy/8+3)*32+sx/8+1]&1023;
            u32 pixel=(sWorldTiles[tile*32+(sy%8)*4+(sx%8)/2]>>((sx&1)*4))&15;
            u32 index=1+(y/8)*28+x/8;
            tiles[index*32+(y%8)*4+(x%8)/2]|=pixel<<((x&1)*4);
            tilemap[(y/8+3)*32+x/8+1]=index|(palette<<12);
        }
        LoadBgTiles(bg,tiles,393*32,0);
    }
    CopyBgTilemapBufferToVram(bg);
}
