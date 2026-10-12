#!/usr/bin/env python3
"""Fixed han-position strata/windows. Context is not part of core denominator."""
import argparse, hashlib, json, random
from pathlib import Path
from analyze_text import normalize,han

def sample(t,seed=20261012,target=600,n=12,context=300):
    positions=[i for i,c in enumerate(t) if han(c)];H=len(positions);rng=random.Random(seed);population=[];chosen=[]
    if not H:return {'population':[],'selected':[],'coverage_han':0,'total_han':0}
    def offset(k):return positions[k] if k<H else len(t)
    for stratum in range(3):
        lo=H*stratum//3;hi=H*(stratum+1)//3;layer=[]
        for j,a in enumerate(range(lo,hi,target)):
            b=min(a+target,hi)
            # Everything before next han belongs to the previous window, except initial prefix.
            start=0 if a==0 else offset(a);end=offset(b)
            row={'id':f'{stratum+1}-{j+1:05d}','stratum':['opening','middle','ending'][stratum],'start':start,'end':end,'han_start':a,'han_end':b,'han_count':b-a,'context_start':0 if a<=context else offset(a-context),'context_end':offset(min(H,b+context))}
            layer.append(row);population.append(row)
        picked=sorted(rng.sample(range(len(layer)),min(n,len(layer))))
        for idx in picked:
            row=dict(layer[idx]);row['inclusion_probability']=min(n,len(layer))/len(layer);row['core']=t[row['start']:row['end']];row['before_context']=t[row['context_start']:row['start']];row['after_context']=t[row['end']:row['context_end']];chosen.append(row)
    return {'algorithm_version':'han-fixed-windows-1.0','seed':seed,'target_han_per_window':target,'requested_per_stratum':n,'context_han_each_side':context,'total_han':H,'population':population,'selected':chosen,'coverage_han':sum(x['han_count'] for x in chosen),'coverage_fraction':sum(x['han_count'] for x in chosen)/H}

def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--encoding',default='utf-8-sig');a=p.parse_args();data=Path(a.input).read_bytes();t=normalize(data.decode(a.encoding,errors='strict'));r=sample(t);r['source_name']=Path(a.input).name;r['normalized_sha256']=hashlib.sha256(t.encode()).hexdigest();r['source_bytes_sha256']=hashlib.sha256(data).hexdigest();Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
