"""Authenticate103 fixes, full objects, event safety and native donor artwork."""
import json
from pathlib import Path
import struct
import unittest

from atlas_surf_overlay import OverlaySource
from atlas_surf_redesign_overlay import load
from atlas_surf_rock_repairs import stage,PLAN,bank_paths
from audit_atlas_rock_fragments import with_layout

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'.local/generated-area-review-src'


@unittest.skipUnless((SOURCE/'.journey-generated-area-review').exists(),'Immutable171 source required')
class CompleteNativeRockRepairs(unittest.TestCase):
    def fixture(self):return load(SOURCE)[0]

    def test_all103_fragments_removed_without_changing_physical_cells_or462_full_boulders(self):
        layer=self.fixture();view=OverlaySource(layer);plan=json.loads(PLAN.read_bytes())
        names={r['map'] for r in plan['repairs']}
        before={n:list(view.words(n)) for n in names};identities=dict(view.identities)
        events={n:view.read('data/maps/'+n+'/map.json') for n in names}
        repaired=stage(layer);after=OverlaySource(layer)
        self.assertEqual(repaired['suspect_pieces_after'],0)
        self.assertEqual(len(repaired['before']['complete_objects']),462)
        self.assertEqual(repaired['before']['complete_objects'],repaired['after']['complete_objects'])
        self.assertEqual(identities,after.identities)
        changed=[]
        for n,words in before.items():
            self.assertEqual(events[n],after.read('data/maps/'+n+'/map.json'))
            for i,(a,b) in enumerate(zip(words,after.words(n))):
                self.assertEqual(a&~1023,b&~1023)
                if a!=b:changed.append((n,i%after.layout(n)['width'],i//after.layout(n)['width']))
        self.assertEqual(set(changed),{(r['map'],*r['tile']) for r in plan['repairs']})
        self.assertEqual(len(changed),103)

    def test_source_drift_is_rejected_before_any_repair(self):
        layer=self.fixture();view=OverlaySource(layer);path=view.layout('Route108')['blockdata_filepath']
        words=list(view.words('Route108'));words[1*view.layout('Route108')['width']+33]=0x593
        layer.stage(path,struct.pack('<'+'H'*len(words),*words))
        with self.assertRaisesRegex(ValueError,'reviewed fragments changed'):stage(layer)

    def test_scripted_layout_repairs_preserve_the_complete_route131_boulder(self):
        layer=self.fixture();view=OverlaySource(layer)
        native=with_layout(view,'Route131','LAYOUT_ROUTE131_SKY_PILLAR')
        whole=[native.word('Route131',x,y) for y in (7,8) for x in (2,3)]
        report=stage(layer)['runtime_variants']
        after=with_layout(OverlaySource(layer),'Route131','LAYOUT_ROUTE131_SKY_PILLAR')
        self.assertEqual(whole,[after.word('Route131',x,y) for y in (7,8) for x in (2,3)])
        self.assertEqual(report['additional_fragments_after'],0)
        self.assertEqual(report['complete_boulders_in_variants_preserved'],56)
        for row in report['repairs']:
            self.assertEqual(after.word(row['map'],*row['tile']),row['after'])

    def test_unreviewed_fragment_in_scripted_layout_rejects_the_batch(self):
        layer=self.fixture();view=with_layout(OverlaySource(layer),'Route131','LAYOUT_ROUTE131_SKY_PILLAR')
        layout=view.layout('Route131');words=list(view.words('Route131'))
        words[7*layout['width']+2]=0x589
        layer.stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(words),*words))
        with self.assertRaisesRegex(ValueError,'variant rock inventory changed'):stage(layer)

    def test_interactive_event_on_a_fragment_is_preserved_by_rejecting_the_batch(self):
        layer=self.fixture();view=OverlaySource(layer);path='data/maps/Route110/map.json'
        mapping=json.loads(view.read(path));mapping['bg_events'].append(dict(x=35,y=31,type='sign',script='ExistingQuest'))
        layer.stage(path,json.dumps(mapping,indent=2)+'\n')
        with self.assertRaisesRegex(ValueError,'overlaps an event'):stage(layer)

    def test_wrong_donor_graphics_cannot_silently_replace_the_whole_small_boulder(self):
        layer=self.fixture();view=OverlaySource(layer);path=bank_paths(view,'gTileset_General')['metatiles']
        raw=view.read(path);data=bytearray(raw)
        data[0x18c*16:0x18c*16+16]=raw[0x193*16:0x193*16+16]
        layer.stage(path,bytes(data))
        with self.assertRaisesRegex(ValueError,'whole-boulder artwork or donor changed'):stage(layer)


if __name__=='__main__':unittest.main()
