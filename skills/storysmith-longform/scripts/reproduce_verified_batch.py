#!/usr/bin/env python3
import argparse,bisect,hashlib,json
from pathlib import Path
from analyze_text import analyze,normalize
from sample_windows import sample

EXPECTED_SOURCE_HASHES={'灵飞经': '3fe02f6a5cf10747d743717d4d0d1a8f50142e706773165808286b9c33fd8552', '十日终焉': '1b769b336572da5cd737d975e1110a561cff27e0de7accf3c80c75bb3e7c37ef', '我不是戏神': '206b1721a4eb46eae94a4e3fe32589b223d9a55d67c7b8c8ad8149aad55097bd'}

EXPECTED_INDEX_HASHES={'灵飞经': {'normalized_path': '3fe02f6a5cf10747d743717d4d0d1a8f50142e706773165808286b9c33fd8552', 'sections_path': 'fef6f1eac6ea7fb74c5e1fc78d0af5a29ca265de2bbe3dc7af3a3d44735305d9', 'paragraphs_path': '8479a61542c231e4e656f98ce80dab53b16e3d52cde6d6cb8f043de499fe52fd'}, '十日终焉': {'normalized_path': '1b769b336572da5cd737d975e1110a561cff27e0de7accf3c80c75bb3e7c37ef', 'sections_path': '1f47b1190dbaedfe03eb91d27a8e81e1b9c007c6ac10794dee06e51bb6afa8ef', 'paragraphs_path': 'c8a150001a74706899c7e5b80263978fa964064b03be8dcd0cdcb83e1080d980'}, '我不是戏神': {'normalized_path': '206b1721a4eb46eae94a4e3fe32589b223d9a55d67c7b8c8ad8149aad55097bd', 'sections_path': '54534ec65f443e64d75c40758d7f1b84b181d7318d61a68dbbcc1ef040777d43', 'paragraphs_path': 'c79d37158df46897b8d06759cead816facfc1ff58773498df8a5d16b94c2143a'}}

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output-dir',required=True);args=p.parse_args();out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True);summary=[]
 for src in json.loads(Path(args.manifest).read_text())['sources']:
  title=src['title'];assert src['original_sha256']==EXPECTED_SOURCE_HASHES.get(title), 'This batch adapter supports only the verified 2026-10-12 source versions; do not reuse hard-coded line boundaries for other editions'
  for key,digest in EXPECTED_INDEX_HASHES[title].items():
   if hashlib.sha256(Path(src[key]).read_bytes()).hexdigest()!=digest:raise ValueError('Source/index bytes differ from verified batch: '+title+' '+key)
  lines=Path(src['normalized_path']).read_text().splitlines();sects=json.loads(Path(src['sections_path']).read_text());paras={r['line']:r for r in map(json.loads,Path(src['paragraphs_path']).read_text().splitlines())};heading_lines={s['line_start'] for s in sects};groups={'main':[],'extra':[],'afterword':[]};starts=[s['line_start'] for s in sects]
  for lineno,line in enumerate(lines,1):
   j=bisect.bisect_right(starts,lineno)-1
   if j<0 or lineno in heading_lines or not line.strip():continue
   sec=sects[j];kind=sec['kind'];group='main' if kind in ('chapter','prologue') else kind
   if title=='十日终焉' and 165150<=lineno<165249:group='afterword'
   if group not in groups:continue
   # Exclude only confirmed terminal marker, never the in-story false ending.
   if (title=='灵飞经' and line.strip()=='（全文终）') or (title=='我不是戏神' and lineno==244141) or (title=='十日终焉' and lineno==165147):continue
   groups[group].append((lineno,line,sec,paras.get(lineno)))
  for group,rows in groups.items():
   if not rows:continue
   chunks=[];mapping=[];pos=0
   for lineno,line,sec,par in rows:
    chunk=normalize(line)+'\n';mapping.append({'start':pos,'end':pos+len(chunk),'source_line':lineno,'section_id':sec['section_id'],'heading':sec['heading'],'paragraph_id':par['id'] if par else None});chunks.append(chunk);pos+=len(chunk)
   t=''.join(chunks);stem=f'{title}.{group}';(out/f'{stem}.analysis.txt').write_text(t);(out/f'{stem}.line_map.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in mapping))
   stats=analyze(t,stem);stats['source_original_sha256']=src['original_sha256'];stats['excluded']='front matter, indexed headings, blank lines, confirmed terminal markers; main/extra/afterword separated';(out/f'{stem}.stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
   if group=='main':
    r=sample(t);r['work']=title;r['normalized_sha256']=hashlib.sha256(t.encode()).hexdigest();r['analysis_text_path']=str(out/f'{stem}.analysis.txt');r['source_original_sha256']=src['original_sha256'];r['offset_semantics']='analysis text Unicode codepoints, half-open; use line_map for original line/paragraph';mapstarts=[m['start'] for m in mapping]
    for w in r['selected']:
     a=max(0,bisect.bisect_right(mapstarts,w['context_start'])-1);b=bisect.bisect_left(mapstarts,w['context_end']);w['source_map']=mapping[a:b]
    r['covered_section_ids']=sorted({m['section_id'] for w in r['selected'] for m in w['source_map'] if m['end']>w['start'] and m['start']<w['end']});r['total_main_sections']=len({x['section_id'] for x in mapping});(out/f'{title}.samples.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));(out/f'{title}.samples.readable.txt').write_text('\n\n'.join(f"WINDOW {w['id']} core=[{w['start']},{w['end']}) han={w['han_count']}\nBEFORE CONTEXT\n{w['before_context']}\nCORE\n{w['core']}\nAFTER CONTEXT\n{w['after_context']}" for w in r['selected']))
    summary.append({'work':title,'han':stats['han'],'sentences':stats['punctuation_sentences'],'sample_han':r['coverage_han'],'coverage_fraction':r['coverage_fraction'],'sample_windows':len(r['selected']),'covered_sections':len(r['covered_section_ids']),'total_sections':r['total_main_sections'],'seed':r['seed']})
   print(stem,stats['han'],flush=True)
 (out/'corpus_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
