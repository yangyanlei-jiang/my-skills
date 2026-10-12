import unittest
from analyze_text import *
class Boundaries(unittest.TestCase):
    def test_han(self):
        self.assertTrue(han('〇'));self.assertTrue(han('𠀀'));self.assertFalse(han('。'));self.assertFalse(han('A'))
    def test_normalize(self):self.assertEqual(normalize('甲\r\n乙\r丙'),'甲\n乙\n丙')
    def test_sentence_and_decimal(self):
        t='他说：“走！快走。”雨停了……\n数为3.14，没错'
        s=sentences(t)
        self.assertEqual([t[a:b] for a,b,_ in s],['他说：“走！','快走。”','雨停了……','数为3.14，没错'])
        self.assertEqual([u[2] for u in s],[False,False,False,True])
    def test_nested_union(self):
        r=analyze('“甲‘乙’丙”丁');self.assertEqual(r['matched_quotation_pairs'],2);self.assertEqual(r['quotation_interior_han_union'],3)
    def test_unclosed_does_not_swallow(self):
        r=analyze('“甲乙。丙丁');self.assertEqual(r['quotation_interior_han_union'],0);self.assertEqual(len(r['quotation_anomalies']),1)
    def test_clause(self):
        t='甲，乙：丙；丁。';self.assertEqual([t[a:b] for a,b in clauses(t,sentences(t))],['甲，','乙：','丙；','丁。'])
    def test_ascii_quote(self):self.assertEqual(analyze('"甲"乙')['quotation_interior_han_union'],1)
    def test_bigram_no_cross(self):
        self.assertEqual(dict(analyze('甲乙，丙丁')['top_adjacent_han_bigrams_not_words']),{'甲乙':1,'丙丁':1})
    def test_empty(self):self.assertEqual(analyze('  \n')['punctuation_sentences'],0)
    def test_punct_only(self):self.assertEqual(analyze('……！')['punctuation_sentences'],0)
    def test_latin(self):self.assertEqual(analyze('Hello!')['sentence_lengths']['han']['zero_count'],1)
    def test_unclosed_outer_closed_inner(self):self.assertEqual(analyze('“甲‘乙’丙')['quotation_interior_han_union'],1)
if __name__=='__main__':unittest.main()
