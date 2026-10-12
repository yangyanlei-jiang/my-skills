import unittest
from sample_windows import sample
class Sampling(unittest.TestCase):
    def test_exhaustive_small(self):
        t='序！甲乙，丙丁。戊己庚辛壬癸';r=sample(t);self.assertEqual(''.join(x['core'] for x in r['selected']),t);self.assertEqual(r['coverage_fraction'],1)
    def test_reproducible(self):
        t='甲乙，丙丁。'*10000;a=sample(t);b=sample(t);self.assertEqual(a,b);self.assertEqual(len(a['selected']),36)
    def test_partition(self):
        t='前文。'+'甲乙，丙丁。'*1000;r=sample(t)
        p=r['population'];self.assertEqual(p[0]['start'],0);self.assertEqual(p[-1]['end'],len(t));self.assertTrue(all(a['end']==b['start'] for a,b in zip(p,p[1:])));self.assertEqual(sum(x['han_count'] for x in p),r['total_han'])
    def test_empty(self):self.assertEqual(sample('abc')['total_han'],0)
if __name__=='__main__':unittest.main()
