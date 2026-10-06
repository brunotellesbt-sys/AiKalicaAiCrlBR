#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/gba/core.h>
#include <mgba/core/log.h>
static void quiet(struct mLogger*l,int c,enum mLogLevel level,const char*f,va_list a){}
static struct mLogger logger={quiet,0};
static struct mCore *core;
static color_t pixels[240*160];
int start(const char *rom) {
 mLogSetDefaultLogger(&logger);
 core=GBACoreCreate(); if(!core || !core->init(core)) return 0;
 mCoreInitConfig(core,"hm-validation");
 core->setVideoBuffer(core,pixels,240);
 if(!mCoreLoadFile(core,rom)) return 0;
 core->reset(core);return 1;
}
void frames(int n, int keys){core->setKeys(core,keys);for(int i=0;i<n;i++)core->runFrame(core);}
unsigned read8(unsigned a){return core->busRead8(core,a);}
unsigned read16(unsigned a){return core->busRead16(core,a);}
unsigned read32(unsigned a){return core->busRead32(core,a);}
void write8(unsigned a,unsigned v){core->busWrite8(core,a,v);}
void write16(unsigned a,unsigned v){core->busWrite16(core,a,v);}
void write32(unsigned a,unsigned v){core->busWrite32(core,a,v);}
void *image(void){return pixels;}
void stop(void){mCoreConfigDeinit(&core->config);core->deinit(core);core=NULL;}
void raw8(unsigned a,unsigned v){core->rawWrite8(core,a,-1,v);}
