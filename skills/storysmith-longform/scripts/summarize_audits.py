#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--results-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args();base=Path(a.results_dir);names=['灵飞经','十日终焉','我不是戏神'];out=['# 模型语义标注测量审计\n','这是创作机制的探索性支撑，不是成稿配方，也不是每次写作必跑流程。语义标签来自模型编码者，不是人类双人。三部上传稿分别36随机窗，每部21,600核心汉字，开/中/末各12窗；独立复核仅每部4窗、2,400汉字。未裁决，保留分歧。\n','## 汇总\n','|材料|修辞跨度/核心汉字|五感跨度/核心汉字|复核修辞F1|复核五感F1|','|---|---:|---:|---:|---:|'];records=[]
 for name in names:
  path=base/f'{name}.annotation_audit.json'
  if not path.exists():out.append(f'|{name}|尚待最终主标|尚待最终主标|—|—|');continue
  r=json.loads(path.read_text());records.append(r)
  f=r['densities']['figurative_all'];s=r['densities']['five_sense_union'];ff=r['blind_pilot']['figurative_all']['f1'];sf=r['blind_pilot']['five_sense_union']['f1'];out.append(f"|{name}|{f['core_han_union']}/{f['denominator_han']}，约{f['raw_per_1000']/10:.1f}%|{s['core_han_union']}/{s['denominator_han']}，约{s['raw_per_1000']/10:.1f}%|{ff:.2f}|{sf:.2f}|")
 out+=['\n## 方法与限制\n','- 以上是确定标签的汉字跨度并集，不是隐喻事件百分比、心理深度或读者注意力。隐喻与明喻分列，总修辞取并集；五感可重叠，温度/内感/运动觉另列。\n- F1按4窗核心汉字集合微平均：2×交集/(主标集合字数+复核集合字数)；Jaccard=交集/并集。双方均空时返回null，不赋完美一致。任一编码者都不是金标准，未算不合适的κ。\n- 完整逐标签原始分子/分母、F1/Jaccard、逐窗交并集及置信区间在每部.annotation_audit.json。bootstrap以窗为簇，在三层内部各自有放回重采样10,000次，seed=20261014；按抽中概率逆权重计算比率。\n- bootstrap仅描述固定这一模型编码版本的抽样波动，不包含标签误差。零正例不输出虚假[0,0]精确区间。稀有标签或单场景承载的结论保留谨慎。\n- 每部4窗pilot小于协议计划的每部8窗，不能代表剩余32窗或全文一致性。五感F1低于0.80门槛时，不能宣传高可靠的感官比例或据此作精细排名。\n- 《十日终焉》4窗修辞F1=1来自仅一条16汉字明喻；隐喻双方零正例，F1未定义。这不证明隐喻编码高度可靠。\n- 版本：十日最初275记录的预冻结审计另存，不作为最终结果；最终270记录来自主标者未读取secondary结果时自行完成的声学边界复查，不是看过复核后的裁决。最终primary副本以.frozen.jsonl保存，审计记录文件SHA。\n','## 未裁决的实际分歧例\n','- 十日1-00103：复核把“冷冷的开口问道”归听觉；主标最终版把它视为情绪归属，不纳入声学。\n- 十日1-00456：复核视觉跨度含笑容、放茶杯、擦黑板这一整串动作，主标较窄。涉及动作是否构成可感知描写和跨度边界。\n- 十日2-00235：主标将设定中的“听到自己内心的声音”归听觉，复核未同标。涉及超常知觉与内心话语的分类。\n- 分歧是需要校准定义的证据，不是悄悄删掉标签抬高分数的理由。若将来裁决，应新建版本，独立一致性仍使用本次原始未裁决记录。\n','## 创作可用性\n','统计→回到证据位置→解释其推进因果/塑造人物/组织信息的功能→提炼适用条件与反例。切勿要求新小说满足某个平均句长、隐喻百分比或感官配比。任何跨书差异同时受题材、叙述环境、情节阶段和模型边界选择影响。\n']
 Path(a.output).write_text('\n'.join(out));(base/'annotation_comparison.raw.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
