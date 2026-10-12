import unittest
from audit_annotations import chars,cover,validate
class Audit(unittest.TestCase):
 def setUp(self):self.t='甲乙，丙丁戊';self.w={'id':'w','start':1,'end':5,'han_count':3}
 def row(self,a,b,l,c='certain'):return {'record_type':'span','window_id':'w','start':a,'end':b,'quote':self.t[a:b],'labels':[l],'certainty':c}
 def test_clip_and_union(self):self.assertEqual(chars([self.row(0,4,'metaphor'),self.row(1,5,'simile')],self.w,self.t,'figurative_all'),{1,3,4})
 def test_uncertain_excluded(self):self.assertEqual(chars([self.row(1,4,'metaphor','uncertain')],self.w,self.t,'metaphor'),set())
 def test_aux_excluded_from_five(self):self.assertEqual(chars([self.row(1,4,'sensory_temperature')],self.w,self.t,'five_sense_union'),set())
 def test_unknown_not_zero(self):self.assertFalse(cover([], 'w','sensory'))
 def test_quote_fail(self):
  r=self.row(1,4,'metaphor');r['quote']='错';self.assertEqual(validate([r],{'w':self.w},self.t,''),[[1,'quote_mismatch']])
if __name__=='__main__':unittest.main()
