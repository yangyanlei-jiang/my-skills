#!/usr/bin/env python3
"""Validate labels, compute descriptive densities and independent raw-span overlap."""
import argparse,collections,hashlib,json,random
from pathlib import Path
from analyze_text import han,quantile
LABELS=['metaphor','simile','sensory_visual','sensory_auditory','sensory_touch','sensory_smell','sensory_taste','sensory_temperature','sensory_interoception','sensory_kinesthetic']
GROUPS={'figurative_all':LABELS[:2],'five_sense_union':LABELS[2:7],'auxiliary_sense_union':LABELS[7:]}

def read(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def cover(records,wid,family):return any(r.get('record_type')=='coverage' and r['window_id']==wid and r.get('status')=='complete' and family in r.get('families_reviewed',[]) for r in records)
def chars(records,w,text,label,uncertain=False):
 result=set();valid=GROUPS.get(label,[label])
 for r in records:
  if r.get('record_type')!='span' or r['window_id']!=w['id']:continue
  if r.get('certainty')!=('uncertain' if uncertain else 'certain'):continue
  if not set(r.get('labels',[r.get('label')]))&set(valid):continue
  result.update(i for i in range(max(w['start'],r['start']),min(w['end'],r['end'])) if han(text[i]))
 return result

def validate(records,windows,text,sha):
 errors=[];keys=set(windows)
 for j,r in enumerate(records,1):
  if r.get('window_id') not in keys:errors.append([j,'unknown_window']);continue
  w=windows[r['window_id']]
  if r.get('sha') and r['sha']!=sha:errors.append([j,'sha_mismatch'])
  if r.get('record_type')=='span':
   a,b=r['start'],r['end']
   if not 0<=a<b<=len(text):errors.append([j,'invalid_bounds'])
   elif r.get('quote')!=text[a:b]:errors.append([j,'quote_mismatch'])
   if b<=w['start'] or a>=w['end']:errors.append([j,'no_core_overlap'])
  elif r.get('record_type')=='coverage' and r.get('core_han') not in (None,w['han_count']):errors.append([j,'core_han_mismatch'])
 return errors

def report(work,primary,secondary,samples,text):
 windows={w['id']:w for w in samples['selected']};sha=hashlib.sha256(text.encode()).hexdigest();primary_path=Path(primary);secondary_path=Path(secondary);primary_hash=hashlib.sha256(primary_path.read_bytes()).hexdigest();secondary_hash=hashlib.sha256(secondary_path.read_bytes()).hexdigest();primary=read(primary);secondary=[r for r in read(secondary) if r['work']==work]
 result={'work':work,'primary_file_sha256':primary_hash,'secondary_file_sha256':secondary_hash,'bootstrap_seed':20261014,'bootstrap_replicates':10000,'coder_identity':'independent model semantic coders; not human annotators','primary_validation_errors':validate(primary,windows,text,sha),'secondary_validation_errors':validate(secondary,windows,text,sha),'primary_records':len(primary),'sample_han':sum(w['han_count'] for w in windows.values()),'coverage':{},'densities':{},'blind_pilot':{},'method':'certain-only han-codepoint sets clipped to core; union within each label; primary density per 1000 core han; overlap F1=2|A∩B|/(|A|+|B|), Jaccard=|A∩B|/|A∪B|. Neither coder is gold. Both empty -> null, not perfect. No adjudication or kappa.'}
 for fam in ['figurative','sensory']:result['coverage'][fam]=sum(cover(primary,w,fam) for w in windows)
 for label in LABELS+list(GROUPS):
  fam='figurative' if label in ['metaphor','simile','figurative_all'] else 'sensory';valid=[w for w in windows.values() if cover(primary,w['id'],fam)];counts={w['id']:len(chars(primary,w,text,label)) for w in valid};den=sum(w['han_count'] for w in valid);num=sum(counts.values());strata=collections.defaultdict(list)
  for w in valid:strata[w['stratum']].append(w)
  def ratio(groups):
   n=d=0
   for group in groups:
    for w in group:n+=counts[w['id']]/w['inclusion_probability'];d+=w['han_count']/w['inclusion_probability']
   return n/d*1000 if d else None
  point=ratio(strata.values());ci=None
  if len(valid)==36 and num>0:
   rng=random.Random(20261014);vals=[]
   for _ in range(10000):vals.append(ratio([rng.choices(v,k=len(v)) for v in strata.values()]))
   ci=[quantile(vals,.025),quantile(vals,.975)]
  result['densities'][label]={'core_han_union':num,'denominator_han':den,'raw_per_1000':num/den*1000 if den else None,'weighted_per_1000':point,'stratified_window_bootstrap_percentile_95':ci,'ci_note':'sampling variability conditional on one coder; not coding-error CI. No finite-population correction; sampling fractions are small. Zero/rare labels require caution. Not a writing target.'}
  A=B=I=U=0;per=[]
  for w in windows.values():
   if not cover(primary,w['id'],fam) or not cover(secondary,w['id'],fam):continue
   a=chars(primary,w,text,label);b=chars(secondary,w,text,label);A+=len(a);B+=len(b);I+=len(a&b);U+=len(a|b);per.append({'window_id':w['id'],'primary_han':len(a),'secondary_han':len(b),'intersection_han':len(a&b),'union_han':len(a|b)})
  result['blind_pilot'][label]={'windows':len(per),'primary_han':A,'secondary_han':B,'intersection_han':I,'union_han':U,'f1':2*I/(A+B) if A+B else None,'jaccard':I/U if U else None,'per_window':per}
 result['uncertain_records']=sum(r.get('record_type')=='span' and r.get('certainty')=='uncertain' for r in primary)
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--primary',required=True);p.add_argument('--secondary',required=True);p.add_argument('--results-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args();base=Path(a.results_dir);sample=json.loads((base/f'{a.work}.samples.json').read_text());t=(base/f'{a.work}.main.analysis.txt').read_text();r=report(a.work,a.primary,a.secondary,sample,t);Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
