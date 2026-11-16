"""A southern ocean loop must preserve the complete existing native terminal."""
import unittest
from atlas_surf_three_port import OPENINGS,extend


class ThreePortTests(unittest.TestCase):
    def fixture(self):
        words=[0x1273]*960
        for x in range(48):words[19*48+x]=0x1643
        for x in range(4,14):words[19*48+x]=0x33a1
        return words

    def test_existing_terminal_and_all_other_cells_are_preserved(self):
        before=self.fixture();after,height=extend(before,48,20,0x1273,0x1643)
        self.assertEqual(height,27);self.assertEqual(len(after),48*27)
        self.assertEqual({(i%48,i//48) for i in range(960) if before[i]!=after[i]},set(OPENINGS))
        self.assertTrue(all(after[19*48+x]==0x33a1 for x in range(4,14)))
        for y in range(20,26):
            self.assertEqual(after[y*48:(y+1)*48],[0x1643]+[0x1273]*46+[0x1643])
        self.assertEqual(after[26*48:],[0x1643]*48)

    def test_changed_openings_and_bad_donors_cannot_delete_an_object(self):
        words=self.fixture();words[19*48+2]=0x33a1
        with self.assertRaisesRegex(ValueError,'authenticated complete reef'):
            extend(words,48,20,0x1273,0x1643)
        for water,reef in [(0x1673,0x1643),(0x3273,0x1643),(0x1273,0x1243)]:
            with self.assertRaises(ValueError):extend(self.fixture(),48,20,water,reef)


if __name__=='__main__':unittest.main()
