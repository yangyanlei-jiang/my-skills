#!/usr/bin/env python3
"""Deterministic mechanical counts only. No literary labels inferred."""
import argparse, collections, hashlib, json, math, re, statistics, unicodedata
from pathlib import Path
VERSION='1.0'
CJK_RANGES=((0x3400,0x4DBF),(0x4E00,0x9FFF),(0xF900,0xFAFF),(0x20000,0x2EBEF),(0x2EBF0,0x2EE5F),(0x2F800,0x2FA1F),(0x30000,0x323AF),(0x323B0,0x3347F))
def han(c):
    n=ord(c)
    return c=='〇' or any(a<=n<=b for a,b in CJK_RANGES)
def normalize(t): return unicodedata.normalize('NFC',t.replace('\r\n','\n').replace('\r','\n'))
def substantive(t): return any(unicodedata.category(c)[0] in 'LN' for c in t)
END=re.compile(r'(?:[。！？!?]+|…{2,}|\.{3,})(?:[。！？!?…]*[”’」』"）)】\]]*)')
def sentences(t):
    out=[]
    offset=0
    for line in t.splitlines(keepends=True):
        start=0
        for m in END.finditer(line):
            if substantive(line[start:m.end()]): out.append((offset+start,offset+m.end(),False))
            start=m.end()
        if substantive(line[start:]): out.append((offset+start,offset+len(line.rstrip('\n')),True))
        offset+=len(line)
    return out

def clauses(t,ss):
    out=[]
    for a,b,_ in ss:
        p=a
        for m in re.finditer('[，,；;：:]',t[a:b]):
            q=a+m.end()
            if substantive(t[p:q]):out.append((p,q))
            p=q
        if substantive(t[p:b]):out.append((p,b))
    return out

def quotation_spans(t):
    pairs={'“':'”','‘':'’','「':'」','『':'』','"':'"'}
    stack=[]; spans=[]; anomalies=[]
    for i,c in enumerate(t):
        if c=='"':
            if stack and stack[-1][0]=='"':
                _,a=stack.pop();spans.append((a+1,i))
            else: stack.append((c,i))
        elif c in pairs:stack.append((c,i))
        elif c in pairs.values():
            if stack and pairs[stack[-1][0]]==c:
                _,a=stack.pop();spans.append((a+1,i))
            else:anomalies.append({'offset':i,'kind':'unmatched_or_misnested_closer','char':c})
    anomalies.extend({'offset':i,'kind':'unclosed_opener','char':c} for c,i in stack)
    return spans,sorted(anomalies,key=lambda x:x['offset'])

def union(spans):
    result=[]
    for a,b in sorted(spans):
        if result and a<=result[-1][1]:result[-1]=(result[-1][0],max(b,result[-1][1]))
        else:result.append((a,b))
    return result

def quantile(v,p):
    if not v:return None
    a=sorted(v);x=(len(a)-1)*p;i=int(x);f=x-i
    return a[i]*(1-f)+a[min(i+1,len(a)-1)]*f

def distribution(v):
    return dict(n=len(v),mean=statistics.mean(v) if v else None,median=statistics.median(v) if v else None,p10=quantile(v,.1),p90=quantile(v,.9),population_stddev=statistics.pstdev(v) if v else None,min=min(v) if v else None,max=max(v) if v else None,zero_count=v.count(0))

def analyze(raw,name=''):
    t=normalize(raw);h=sum(map(han,t));ss=sentences(t);cs=clauses(t,ss)
    spans,errors=quotation_spans(t);qh=sum(sum(map(han,t[a:b])) for a,b in union(spans))
    punct=collections.Counter(c for c in t if unicodedata.category(c).startswith('P') or c=='…')
    chars=collections.Counter(c for c in t if han(c))
    bigrams=collections.Counter(t[i:i+2] for i in range(len(t)-1) if han(t[i]) and han(t[i+1]))
    def lengths(units):
        return {'han':distribution([sum(map(han,t[a:b])) for a,b,*_ in units]),'nonwhitespace_codepoints':distribution([sum(not c.isspace() for c in t[a:b]) for a,b,*_ in units])}
    return {'algorithm_version':VERSION,'source_name':name,'scope':'uploaded material only; completeness not inferred','normalized_sha256':hashlib.sha256(t.encode()).hexdigest(),'normalized_codepoints':len(t),'han':h,'nonwhitespace_codepoints':sum(not c.isspace() for c in t),'physical_nonempty_lines':sum(bool(x.strip()) for x in t.splitlines()),'punctuation_sentences':len(ss),'unterminated_fragments':sum(x[2] for x in ss),'clauses':len(cs),'sentence_lengths':lengths(ss),'clause_lengths':lengths(cs),'matched_quotation_pairs':len(spans),'quotation_interior_han_union':qh,'quotation_han_fraction':qh/h if h else None,'quotation_anomalies':errors,'punctuation':{c:{'count':n,'per_1000_han':n*1000/h if h else None} for c,n in sorted(punct.items())},'top_han':chars.most_common(50),'top_adjacent_han_bigrams_not_words':bigrams.most_common(100)}

def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--encoding',default='utf-8-sig');a=p.parse_args()
    data=Path(a.input).read_bytes();raw=data.decode(a.encoding,errors='strict');r=analyze(raw,Path(a.input).name);r['source_bytes_sha256']=hashlib.sha256(data).hexdigest();r['decoding']=a.encoding
    Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
