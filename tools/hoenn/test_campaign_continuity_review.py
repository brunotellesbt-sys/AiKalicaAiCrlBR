"""Exercise the actual campaign selector with the actual actor visibility guard."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from campaign_continuity_review import ACTORS, GATES, HEADER, SHELLY_NEW, repair

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT/'tools/hoenn/data/campaign-continuity-reference.json'


def function(text, name):
    start = re.search(r'^(?:static )?(?:bool32|u32) '+name+r'\([^)]*\)\s*\{',text,re.M)
    assert start, name
    end,depth = start.end(),1
    while depth:
        depth += (text[end]=='{')-(text[end]=='}')
        end += 1
    return text[start.start():end]


class CampaignContinuity(unittest.TestCase):
    def fixture(self):
        reference = json.loads(REFERENCE.read_bytes())
        for path,text in reference['source'].items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),reference['sha256'][path])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        source = Path(directory.name)
        for name,text in reference['source'].items():
            p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        class Stage:
            outputs = {}
            expected = reference['sha256']
            def __init__(self): self.source=source
            def stage(self,name,raw):self.outputs[name]=raw.encode() if isinstance(raw,str) else raw
        return Stage(),reference

    def observed_cases(self, data, directory):
        selector = function(data[GATES], 'JourneyPendingCampaignEvent')
        visible = function(data[ACTORS], 'JourneyStoryObjectVisible')
        names = sorted(set(re.findall(r'\b(?:FLAG|VAR)_[A-Z0-9_]+', selector+visible)))
        labels = sorted(set(re.findall(r'script==(\w+)',visible)))
        declarations='''#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32,bool32; typedef int16_t s16;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
'''+''.join(f'#define {name} {i+1}\n' for i,name in enumerate(names))+data[HEADER]+'''
static u32 badges, weatherComplete, crisis;
struct JourneyTeamMission {bool32 kanto;u8 badges,event;};
static const struct JourneyTeamMission sJourneyTeamMissions[]={{FALSE,4,12}};
static u32 JourneyGymBadgeCount(bool32 kanto){(void)kanto;return badges;}
static u32 JourneyNativeCampaignEvent(bool32 kanto,u32 count){(void)kanto;(void)count;return 0;}
static bool32 JourneyMissionComplete(const struct JourneyTeamMission *m){(void)m;return TRUE;}
static bool32 JourneyWeatherInstituteComplete(void){return weatherComplete;}
static bool32 JourneyAquaHideoutComplete(void){return TRUE;}
static bool32 JourneySpaceCenterComplete(void){return TRUE;}
static bool32 RegionalFlag(u16 flag){return flag==FLAG_SYS_WEATHER_CTRL?crisis:TRUE;}
static bool32 FlagGet(u16 flag){(void)flag;return TRUE;}
static u32 VarGet(u16 var){(void)var;return 0;}
'''+''.join(f'const u8 {label}[]={{ {i+1} }};\n' for i,label in enumerate(labels))
        main='''
int main(void){
 const u32 cases[][3]={{3,0,0},{4,0,0},{4,1,0},{7,1,1}};
 for(unsigned i=0;i<ARRAY_COUNT(cases);i++){
  badges=cases[i][0];weatherComplete=cases[i][1];crisis=cases[i][2];
  printf("%u %u\\n",JourneyPendingCampaignEvent(FALSE),
    JourneyStoryObjectVisible(Route119_WeatherInstitute_2F_EventScript_Shelly));
 }
 return 0;
}
'''
        path=Path(directory)/'case.c';binary=Path(directory)/'case'
        path.write_text(declarations+selector+'\n'+visible+'\n'+main)
        subprocess.run([shutil.which('cc'),'-std=c11','-Wall','-Wextra','-Werror',str(path),'-o',str(binary)],
                       capture_output=True,check=True)
        result=subprocess.check_output([str(binary)],text=True)
        return [tuple(map(int,row.split())) for row in result.splitlines()]

    def test_actual_selector_and_visibility_reproduce_parent_softlock_and_repair(self):
        layer,reference=self.fixture()
        self.assertEqual(self.observed_cases(reference['source'],layer.source),
                         [(0,0),(15,0),(0,0),(14,1)])
        report=repair(layer)
        fixed={name:raw.decode() for name,raw in layer.outputs.items()}
        self.assertEqual(self.observed_cases(fixed,layer.source),
                         [(0,0),(15,1),(0,0),(14,0)])
        self.assertEqual(set(layer.outputs),{HEADER,GATES,ACTORS})
        self.assertEqual(report['corrected_visibility_event'],15)
        for path,text in reference['source'].items():
            self.assertEqual((layer.source/path).read_text(),text)

    def test_unexpected_actor_checkpoint_is_rejected_before_staging(self):
        layer,reference=self.fixture()
        path=layer.source/ACTORS
        path.write_text(reference['source'][ACTORS].replace('==14;', '==17;'))
        layer.expected=dict(layer.expected)
        layer.expected[ACTORS]=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(AssertionError):repair(layer)
        self.assertEqual(layer.outputs,{})

    def test_unrelated_actor_visibility_is_preserved(self):
        layer,reference=self.fixture()
        repair(layer)
        before=reference['source'][ACTORS]
        after=layer.outputs[ACTORS].decode()
        self.assertEqual(after.replace(SHELLY_NEW,SHELLY_NEW.replace('==JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE;', '==14;')),before)

    def test_real_completion_predicate_keeps_clear_after_native_route119_state2(self):
        layer,reference=self.fixture()
        repair(layer)
        setup='''#include <stdio.h>
typedef unsigned bool32,u16;
#define VAR_WEATHER_INSTITUTE_STATE 1
#define TRAINER_FLAGS_START 1280
#define TRAINER_SHELLY_WEATHER_INSTITUTE 32
static unsigned state,defeated;
static unsigned VarGet(u16 id){(void)id;return state;}
static bool32 RegionalFlag(u16 id){(void)id;return defeated;}
'''
        main='''int main(void){
 const unsigned cases[][2]={{0,0},{0,1},{1,0},{1,1},{2,1},{2,0}};
 for(unsigned i=0;i<6;i++){state=cases[i][0];defeated=cases[i][1];
 printf("%u\\n",JourneyWeatherInstituteComplete());}return 0;}
'''
        outputs=[]
        for source in (reference['source'][GATES],layer.outputs[GATES].decode()):
            p=layer.source/'complete.c';binary=layer.source/'complete'
            p.write_text(setup+function(source,'JourneyWeatherInstituteComplete')+main)
            subprocess.run([shutil.which('cc'),'-std=c11','-Wall','-Wextra','-Werror',str(p),'-o',str(binary)],check=True)
            outputs.append(list(map(int,subprocess.check_output([str(binary)],text=True).split())))
        self.assertEqual(outputs[0],[0,0,0,1,0,0])
        self.assertEqual(outputs[1],[0,0,0,1,1,0])


if __name__=='__main__':unittest.main()
