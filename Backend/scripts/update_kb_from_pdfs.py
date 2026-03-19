# -*- coding: utf-8 -*-
"""
PDF 解析结果写入知识库脚本
- 更新 parsed_text_index.csv、parse_report.md
- 新增 PDF 来源的 evidence、rules、thresholds
- 写入 evidence_master.csv、rule_master.csv、rule_threshold.csv、kb.sqlite
"""
import sys, csv, sqlite3, pathlib, datetime
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = pathlib.Path(__file__).parent.parent / "knowledge_base"
PARSED_DIR = ROOT / "parsed_text"
TODAY = datetime.date.today().isoformat()

# ─── 1. 更新 parsed_text_index.csv ────────────────────────────
idx_path = PARSED_DIR / "parsed_text_index.csv"
fields = ["source_id","title","source_path","parsed_txt_path","text_length","parse_status"]

# Read existing
existing = {}
with open(idx_path, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        existing[row["source_id"]] = row

# PDF results
pdf_updates = {
    "HLJ-004": {
        "source_id": "HLJ-004",
        "title": "2026年黑龙江省农作物主要病虫草鼠害防控指导意见（PDF附件）",
        "source_path": "knowledge_base/raw_sources/hlj/2026_黑龙江农作物主要病虫草鼠害防控指导意见.pdf",
        "parsed_txt_path": "",
        "text_length": 0,
        "parse_status": "image_scan_no_text_layer",
    },
    "HLJ-005": {
        "source_id": "HLJ-005",
        "title": "2025年黑龙江省农业主推技术",
        "source_path": "knowledge_base/raw_sources/hlj/2025_黑龙江农业主推技术.pdf",
        "parsed_txt_path": "knowledge_base/parsed_text/HLJ-005.txt",
        "text_length": (PARSED_DIR / "HLJ-005.txt").stat().st_size if (PARSED_DIR / "HLJ-005.txt").exists() else 0,
        "parse_status": "ok_partial_soybean_pages",
    },
    "HLJ-006": {
        "source_id": "HLJ-006",
        "title": "2025年黑龙江省农作物栽培技术模式汇编",
        "source_path": "knowledge_base/raw_sources/hlj/2025_黑龙江农作物栽培技术模式汇编.pdf",
        "parsed_txt_path": "knowledge_base/parsed_text/HLJ-006.txt",
        "text_length": (PARSED_DIR / "HLJ-006.txt").stat().st_size if (PARSED_DIR / "HLJ-006.txt").exists() else 0,
        "parse_status": "ok_partial_soybean_pages",
    },
    "HLJ-007": {
        "source_id": "HLJ-007",
        "title": "黑龙江省2025年科学施肥增效项目实施方案",
        "source_path": "knowledge_base/raw_sources/hlj/2025_黑龙江科学施肥增效项目实施方案.pdf",
        "parsed_txt_path": "knowledge_base/parsed_text/HLJ-007.txt",
        "text_length": (PARSED_DIR / "HLJ-007.txt").stat().st_size if (PARSED_DIR / "HLJ-007.txt").exists() else 0,
        "parse_status": "ok",
    },
}
for sid, upd in pdf_updates.items():
    existing[sid] = upd

with open(idx_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for row in sorted(existing.values(), key=lambda x: x["source_id"]):
        w.writerow(row)
print(f"  parsed_text_index.csv updated: {len(existing)} rows")

# ─── 2. 新增 evidence 条目（来自 PDF 内容）──────────────────────
NEW_EVIDENCE = [
    # ════ HLJ-005：2025黑龙江农业主推技术 ════
    {
        "evidence_id": "EV-028",
        "source_id": "HLJ-005",
        "page_or_section": "大豆根瘤菌科学施肥技术（第28项）",
        "topic": "根瘤菌接种",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种前-全生育期",
        "evidence_text": (
            "选用质量合格的根瘤菌菌剂，产品质量符合《农用微生物菌剂》（GB 20287）要求。"
            "根瘤菌接种可提高有效根瘤形成，促进大豆生物形状和产量提升；"
            "通过替代部分氮肥，增加有机肥和微量元素肥料，有效减少不合理氮肥投入，"
            "提高化肥利用率。2022年以来，在全省推广应用大豆根瘤菌科学施肥技术1640万亩以上，"
            "较常规施肥平均单株荚数增加2.7个。"
        ),
        "normalized_action": "选用符合GB 20287标准的根瘤菌菌剂；接种可减少氮肥投入，增加有效根瘤数量",
        "evidence_level": "A",
        "trigger_hint": "播种前/根瘤菌接种配套施肥",
        "notes": "2025年黑龙江省农业主推技术第28项，省级推广验证，1640万亩应用规模",
    },
    {
        "evidence_id": "EV-029",
        "source_id": "HLJ-005",
        "page_or_section": "大豆全程养分管理技术（第30项）",
        "topic": "施肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "全生育期",
        "evidence_text": (
            "大豆'两增一减'施肥核心技术：以测土配方施肥精准匹配底肥为基础，"
            "利用缓控释肥、有机无机复合肥等提高肥料利用效率，减少化肥总体用量，"
            "同时以根瘤菌剂、叶面肥等辅助手段提升产量和品质。"
            "分层施肥：种肥施在种下5cm处，底肥施在种下10～12cm处，"
            "氮磷钾比例控制在1:1.1-1.5:0.8-1.2，控释氮肥比例不低于30%。"
            "叶面肥以补充中、微量元素为主，在花期、荚期、鼓粒期适时喷施。"
        ),
        "normalized_action": (
            "分层施肥：种肥种下5cm+底肥种下10-12cm；N:P:K=1:1.1-1.5:0.8-1.2；"
            "控释氮肥≥30%；花期/荚期/鼓粒期喷施中微量叶面肥"
        ),
        "evidence_level": "A",
        "trigger_hint": "播种期施肥方案/叶面肥时机",
        "notes": "2025年黑龙江省农业主推技术第30项，测土配方+分层施肥+缓控释肥集成方案",
    },
    {
        "evidence_id": "EV-030",
        "source_id": "HLJ-005",
        "page_or_section": "大豆高效固氮施肥技术（第31项）",
        "topic": "施肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种期",
        "evidence_text": (
            "采用玉米-大豆轮作种植模式，大豆生长发育时期根据地区实际情况适时合理高效施用化肥。"
            "中等肥力地块一般尿素（N：46%）30～50kg/hm²、"
            "氯化钾（K₂O：50%）75～100kg/hm²，"
            "磷酸二铵（N：18%，P₂O₅：46%）180～200kg/hm²。"
            "该技术可减少氮肥施用量10%，有效根瘤数量增加15-20%，"
            "根瘤固氮能力提升10-30%，实现增产7-12%，籽粒蛋白质含量提升1个单位。"
        ),
        "normalized_action": (
            "玉米-大豆轮作中等肥力地块：尿素30-50 kg/hm²，KCl 75-100 kg/hm²，"
            "磷酸二铵180-200 kg/hm²；轮作减氮10%，配套根瘤菌接种"
        ),
        "evidence_level": "A",
        "trigger_hint": "轮作地块/播种期施肥量参考",
        "notes": "2025年黑龙江省农业主推技术第31项，国家重点研发计划成果",
    },
    {
        "evidence_id": "EV-031",
        "source_id": "HLJ-005",
        "page_or_section": "大豆窄行密植与黑土保护耕种技术（第32项）",
        "topic": "中后期田间管理",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种期",
        "evidence_text": (
            "大垄种植地块采取分层施肥方式，第一层占施肥量的1/3，施肥深度10～12cm，"
            "第二层占施肥量的2/3，施肥深度16～18cm；"
            "平作少耕地块的施肥采取春季播种时一次性施入种肥方式，"
            "施肥部位位于种侧5～7cm。"
        ),
        "normalized_action": (
            "大垄：1/3底肥深10-12cm + 2/3底肥深16-18cm（分层施肥）；"
            "平作少耕：种侧5-7cm一次性种肥"
        ),
        "evidence_level": "A",
        "trigger_hint": "大垄/平作施肥深度与位置",
        "notes": "2025年黑龙江省农业主推技术第32项，明确分层施肥比例和深度",
    },
    # ════ HLJ-006：2025黑龙江农作物栽培技术模式汇编 ════
    {
        "evidence_id": "EV-032",
        "source_id": "HLJ-006",
        "page_or_section": "大豆垄三高产优质栽培技术模式（第十一章）",
        "topic": "施肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种期",
        "evidence_text": (
            "大豆'垄三'栽培模式：三垄（垄体播种、垄沟深松、垄上深施肥）。"
            "施肥量根据土壤肥力确定，采用测土配方施肥，"
            "一般每公顷施纯N 25～40kg、P₂O₅ 60～90kg、K₂O 30～50kg。"
            "磷肥全部作底肥施用；氮肥、钾肥按'底肥50%+追肥50%'或'底肥70%+追肥30%'分施。"
        ),
        "normalized_action": (
            "垄三模式：N 25-40 kg/hm²，P₂O₅ 60-90 kg/hm²，K₂O 30-50 kg/hm²；"
            "磷全部底施；氮钾底肥50-70%+追肥30-50%"
        ),
        "evidence_level": "A",
        "trigger_hint": "垄三栽培/播种期施肥量",
        "notes": "2025年黑龙江省农作物栽培技术模式汇编第十一章，含N/P/K具体用量范围",
    },
    {
        "evidence_id": "EV-033",
        "source_id": "HLJ-006",
        "page_or_section": "大豆全生育期叶面一喷多促技术模式（第十四章）",
        "topic": "追肥/叶面肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "初花期-鼓粒期",
        "evidence_text": (
            "大豆全生育期'一喷多促'技术：在大豆初花期（R1）、盛花期（R2）、"
            "结荚期（R3-R4）、鼓粒期（R5-R6）分别喷施。"
            "喷施内容根据生育期确定：初花期喷施硼、钼微量元素+磷酸二氢钾；"
            "鼓粒期喷施氨基酸类叶面肥+磷酸二氢钾，每次喷施用水量不少于30L/亩。"
            "每次间隔7～10天，可与农药混施实现'一喷多防'。"
        ),
        "normalized_action": (
            "一喷多促：R1初花期喷硼钼+磷酸二氢钾；R5-R6鼓粒期喷氨基酸+磷酸二氢钾；"
            "每次≥30L/亩，间隔7-10天，可与农药混施"
        ),
        "evidence_level": "A",
        "trigger_hint": "初花期至鼓粒期叶面肥/一喷多促",
        "notes": "2025年黑龙江省农作物栽培技术模式汇编第十四章",
    },
    {
        "evidence_id": "EV-034",
        "source_id": "HLJ-006",
        "page_or_section": "大豆种子包衣防病技术模式（第十六章）",
        "topic": "病虫害防控",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种前",
        "evidence_text": (
            "大豆种子包衣防病技术：选用含有精甲霜灵·咯菌腈的复合种衣剂，"
            "防治大豆根腐病、苗期立枯病等土传病害。"
            "推荐使用复合型种衣剂（杀菌+杀虫），同时兼防地下害虫（蛴螬、金针虫）。"
            "包衣时在阴凉通风处操作，包衣后晾干再播种，避免阳光直射。"
            "推荐种衣剂用量：每100kg种子用有效成分含量符合要求的种衣剂按标签说明使用。"
        ),
        "normalized_action": (
            "选用精甲霜灵·咯菌腈复合种衣剂包衣；杀菌+杀虫兼防；"
            "阴凉处包衣，晾干后播种"
        ),
        "evidence_level": "A",
        "trigger_hint": "播种前种子处理/根腐病防控",
        "notes": "2025年黑龙江省农作物栽培技术模式汇编第十六章",
    },
    {
        "evidence_id": "EV-035",
        "source_id": "HLJ-006",
        "page_or_section": "大豆根瘤菌接种及配套施肥技术模式（第十七章）",
        "topic": "根瘤菌接种",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种前",
        "evidence_text": (
            "根瘤菌接种技术要点：选用已取得农业农村部登记的大豆根瘤菌剂产品，"
            "产品质量符合《农用微生物菌剂》（GB 20287）国家标准。"
            "液体菌剂拌种：播种前2小时内完成拌种，避免阳光直射，随拌随播。"
            "固体菌剂包衣：将菌剂与粘合剂混合后包裹种子，阴凉处晾干备播。"
            "接种后不得与杀菌剂混用，如需使用杀菌剂种衣剂应先包衣晾干再接种。"
        ),
        "normalized_action": (
            "液体菌剂：播前2小时内拌种，随拌随播；"
            "固体包衣：与粘合剂混合包衣，阴凉晾干；"
            "接种后不与杀菌剂混用"
        ),
        "evidence_level": "A",
        "trigger_hint": "根瘤菌接种操作规范/与杀菌剂间隔",
        "notes": "2025年黑龙江省农作物栽培技术模式汇编第十七章，补充了液体/固体菌剂操作区别",
    },
    # ════ HLJ-007：2025黑龙江科学施肥增效项目实施方案 ════
    {
        "evidence_id": "EV-036",
        "source_id": "HLJ-007",
        "page_or_section": "重点任务-三新集成模式推广",
        "topic": "施肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "播种期",
        "evidence_text": (
            "大豆重点集成推广'根瘤菌剂+分层施肥'技术模式。"
            "分层施肥：种肥施在种下5cm处，底肥施在种下10～12cm处，"
            "肥料采用大豆专用肥料，氮磷钾比例控制范围在1:1.1-1.5:0.8-1.2，"
            "具体施用量以当地情况调整，控释氮肥比例不低于30%。"
        ),
        "normalized_action": (
            "大豆推广'根瘤菌剂+分层施肥'：种肥种下5cm+底肥种下10-12cm；"
            "N:P:K=1:1.1-1.5:0.8-1.2；控释氮肥≥30%"
        ),
        "evidence_level": "A",
        "trigger_hint": "省级重点推广技术/播种期施肥",
        "notes": "黑龙江省2025年科学施肥增效项目实施方案，农业农村厅下发文件",
    },
    {
        "evidence_id": "EV-037",
        "source_id": "HLJ-007",
        "page_or_section": "巩固提升测土配方施肥-田间试验",
        "topic": "施肥",
        "crop": "大豆",
        "region": "黑龙江省",
        "growth_stage": "全生育期",
        "evidence_text": (
            "大豆根瘤菌试验每个补贴6000元，于2025年10月底前完成。"
            "围绕施肥新技术、新产品、新机具，开展新型肥料、施肥效应、配方校正和大豆根瘤菌等田间试验。"
            "通过田间试验监测土壤养分、施肥效果、产量水平变化，用可靠数据评价科学施肥效果。"
        ),
        "normalized_action": "开展大豆根瘤菌+施肥效应田间试验，监测养分、施肥效果、产量变化",
        "evidence_level": "A",
        "trigger_hint": "根瘤菌接种配套施肥效果评价",
        "notes": "黑龙江省2025年科学施肥增效项目实施方案，说明省级田间试验部署",
    },
]

# ─── 3. 新增 rules（基于新 evidence）───────────────────────────
NEW_RULES = [
    {
        "rule_id": "R-F-006",
        "rule_name": "分层施肥技术推荐",
        "trigger_type": "生育期提醒",
        "growth_stage": "播种期",
        "condition_expr": "growth_stage == '播种期'",
        "advice_text": (
            "【分层施肥建议】推荐采用大豆专用分层施肥技术："
            "种肥施在种下5cm处，底肥施在种下10～12cm处（大垄可分两层：1/3在10-12cm，2/3在16-18cm）。"
            "肥料氮磷钾比例建议1:1.1-1.5:0.8-1.2，控释氮肥比例不低于30%。"
            "具体用量参照测土配方结果，中等肥力地块可参考N 30-50 kg/hm²。"
        ),
        "advice_type": "处方",
        "source_id": "HLJ-005;HLJ-007",
        "evidence_id": "EV-029;EV-036",
        "evidence_level": "A",
        "version": "1.0",
        "is_active": 1,
    },
    {
        "rule_id": "R-F-007",
        "rule_name": "一喷多促叶面肥方案",
        "trigger_type": "生育期提醒",
        "growth_stage": "初花期-鼓粒期",
        "condition_expr": "growth_stage in ('初花期','盛花期','结荚期','鼓粒期')",
        "advice_text": (
            "【一喷多促提示】推荐按大豆全生育期'一喷多促'方案：\n"
            "初花期（R1）：喷施硼钼微量元素+磷酸二氢钾；\n"
            "结荚期（R3-R4）：根据长势选择叶面肥；\n"
            "鼓粒期（R5-R6）：喷施氨基酸类叶面肥+磷酸二氢钾。\n"
            "每次喷施用水量不少于30L/亩，间隔7～10天，可与农药混施实现'一喷多防'。"
        ),
        "advice_type": "提示",
        "source_id": "HLJ-006",
        "evidence_id": "EV-033",
        "evidence_level": "A",
        "version": "1.0",
        "is_active": 1,
    },
    {
        "rule_id": "R-N-003",
        "rule_name": "根瘤菌菌剂选用与接种操作规范",
        "trigger_type": "生育期提醒",
        "growth_stage": "播种前",
        "condition_expr": "growth_stage == '播种前'",
        "advice_text": (
            "【根瘤菌接种操作规范】选用已取得农业农村部登记、符合GB 20287标准的根瘤菌菌剂。\n"
            "液体菌剂：播前2小时内拌种，避免阳光直射，随拌随播。\n"
            "固体包衣型：与粘合剂混合包裹种子，阴凉处晾干后播种。\n"
            "注意：接种后不得与杀菌剂混用；如需使用杀菌剂种衣剂，须先完成包衣晾干后再接种根瘤菌。"
        ),
        "advice_type": "处方",
        "source_id": "HLJ-006;HLJ-005",
        "evidence_id": "EV-035;EV-028",
        "evidence_level": "A",
        "version": "1.0",
        "is_active": 1,
    },
]

# ─── 4. 新增 thresholds ───────────────────────────────────────
NEW_THRESHOLDS = [
    {
        "threshold_id": "TH-011",
        "rule_id": "R-F-006",
        "metric": "N_per_hm2_rotation",
        "comparator": "range",
        "value": "30-50",
        "unit": "kg/hm²（尿素折纯N）",
        "value_source": "固定阈值（HLJ-005 2025年主推技术第31项）",
        "evidence_ids": "EV-030",
        "notes": "玉米-大豆轮作中等肥力地块参考值",
    },
    {
        "threshold_id": "TH-012",
        "rule_id": "R-F-006",
        "metric": "controlled_release_N_ratio",
        "comparator": ">=",
        "value": "30",
        "unit": "%（占氮肥总量）",
        "value_source": "固定阈值（HLJ-007 省级施肥增效方案）",
        "evidence_ids": "EV-036",
        "notes": "控释氮肥比例不低于30%",
    },
    {
        "threshold_id": "TH-013",
        "rule_id": "R-F-007",
        "metric": "foliar_spray_volume_per_mu",
        "comparator": ">=",
        "value": "30",
        "unit": "L/亩",
        "value_source": "固定阈值（HLJ-006 2025年栽培技术模式汇编）",
        "evidence_ids": "EV-033",
        "notes": "一喷多促每次喷施用水量不少于30L/亩",
    },
    {
        "threshold_id": "TH-014",
        "rule_id": "R-F-007",
        "metric": "foliar_spray_interval_days",
        "comparator": "range",
        "value": "7-10",
        "unit": "天",
        "value_source": "固定阈值（HLJ-006 2025年栽培技术模式汇编）",
        "evidence_ids": "EV-033",
        "notes": "一喷多促间隔天数",
    },
    {
        "threshold_id": "TH-015",
        "rule_id": "R-N-003",
        "metric": "inoculation_timing_h_liquid",
        "comparator": "<=",
        "value": "2",
        "unit": "小时（播前，液体菌剂）",
        "value_source": "固定阈值（HLJ-006 2025年栽培技术模式汇编）",
        "evidence_ids": "EV-035",
        "notes": "液体根瘤菌剂播前2小时内拌种（MOA-001要求≤12小时，此处更严格）",
    },
]

# ─── 5. 读取现有数据并追加 ────────────────────────────────────
EV_PATH = ROOT / "evidence_master.csv"
RM_PATH = ROOT / "rule_master.csv"
RT_PATH = ROOT / "rule_threshold.csv"
DB_PATH = ROOT / "kb.sqlite"

EV_FIELDS = ["evidence_id","source_id","page_or_section","topic","crop","region",
             "growth_stage","evidence_text","normalized_action","evidence_level",
             "trigger_hint","notes"]
RM_FIELDS = ["rule_id","rule_name","trigger_type","growth_stage","condition_expr",
             "advice_text","advice_type","source_id","evidence_id",
             "evidence_level","version","is_active"]
RT_FIELDS = ["threshold_id","rule_id","metric","comparator","value","unit",
             "value_source","evidence_ids","notes"]

# Read existing
def read_csv(path, fields):
    existing = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = row[fields[0]]
            existing[key] = row
    return existing

ev_existing = read_csv(EV_PATH, EV_FIELDS)
rm_existing = read_csv(RM_PATH, RM_FIELDS)
rt_existing = read_csv(RT_PATH, RT_FIELDS)

# Add new (skip if already exists)
new_ev_added = 0
for ev in NEW_EVIDENCE:
    if ev["evidence_id"] not in ev_existing:
        ev_existing[ev["evidence_id"]] = ev
        new_ev_added += 1

new_ru_added = 0
for ru in NEW_RULES:
    if ru["rule_id"] not in rm_existing:
        rm_existing[ru["rule_id"]] = ru
        new_ru_added += 1

new_th_added = 0
for th in NEW_THRESHOLDS:
    if th["threshold_id"] not in rt_existing:
        rt_existing[th["threshold_id"]] = th
        new_th_added += 1

# Write CSV
def write_csv(path, rows_dict, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in sorted(rows_dict.values(), key=lambda x: x[fields[0]]):
            w.writerow(row)

write_csv(EV_PATH, ev_existing, EV_FIELDS)
write_csv(RM_PATH, rm_existing, RM_FIELDS)
write_csv(RT_PATH, rt_existing, RT_FIELDS)

print(f"  evidence_master.csv: {len(ev_existing)} rows (+{new_ev_added} new)")
print(f"  rule_master.csv:     {len(rm_existing)} rows (+{new_ru_added} new)")
print(f"  rule_threshold.csv:  {len(rt_existing)} rows (+{new_th_added} new)")

# ─── 6. 写入 SQLite ──────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Re-create and reload evidence
cur.execute("DROP TABLE IF EXISTS evidence")
cur.execute("""
CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY,
    source_id TEXT, page_or_section TEXT, topic TEXT,
    crop TEXT, region TEXT, growth_stage TEXT,
    evidence_text TEXT, normalized_action TEXT,
    evidence_level TEXT, trigger_hint TEXT, notes TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
)""")
for row in ev_existing.values():
    cur.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(row[f] for f in EV_FIELDS))

# Re-create and reload rules
cur.execute("DROP TABLE IF EXISTS rules")
cur.execute("""
CREATE TABLE rules (
    rule_id TEXT PRIMARY KEY, rule_name TEXT, trigger_type TEXT,
    growth_stage TEXT, condition_expr TEXT, advice_text TEXT,
    advice_type TEXT, source_id TEXT, evidence_id TEXT,
    evidence_level TEXT, version TEXT, is_active INTEGER
)""")
for row in rm_existing.values():
    cur.execute("INSERT INTO rules VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(row[f] for f in RM_FIELDS))

# Re-create and reload thresholds
cur.execute("DROP TABLE IF EXISTS thresholds")
cur.execute("""
CREATE TABLE thresholds (
    threshold_id TEXT PRIMARY KEY, rule_id TEXT, metric TEXT,
    comparator TEXT, value TEXT, unit TEXT,
    value_source TEXT, evidence_ids TEXT, notes TEXT,
    FOREIGN KEY (rule_id) REFERENCES rules(rule_id)
)""")
for row in rt_existing.values():
    cur.execute("INSERT INTO thresholds VALUES (?,?,?,?,?,?,?,?,?)",
        tuple(row[f] for f in RT_FIELDS))

conn.commit()
conn.close()
print(f"  kb.sqlite: evidence={len(ev_existing)}, rules={len(rm_existing)}, thresholds={len(rt_existing)}")

# ─── 7. 更新 parse_report.md ─────────────────────────────────
sm_path = ROOT / "source_master.csv"
src_map = {}
with open(sm_path, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        src_map[row["source_id"]] = row

parse_lines = [
    "# HTML/PDF 正文解析报告",
    f"**生成日期：** {TODAY}（含PDF解析更新）",
    "",
    "## 解析结果汇总",
    "",
    "| source_id | 文件名 | 解析状态 | 字符数 | 说明 |",
    "|-----------|--------|---------|-------|------|",
]
for sid in sorted(existing.keys()):
    row = existing[sid]
    fname = src_map.get(sid, {}).get("file_name", "")[:45]
    status = row["parse_status"]
    tlen = int(row.get("text_length", 0)) if row.get("text_length") else 0
    note_map = {
        "ok": "成功",
        "ok_partial_soybean_pages": "PDF成功（大豆相关页）",
        "skipped_pdf": "PDF跳过（旧状态）",
        "image_scan_no_text_layer": "图像扫描件，无文本层",
        "file_not_found": "文件未找到",
    }
    note = note_map.get(status, status)
    parse_lines.append(f"| {sid} | {fname} | {status} | {tlen:,} | {note} |")

ok_cnt = sum(1 for r in existing.values() if r["parse_status"] in ("ok","ok_partial_soybean_pages"))
skip_cnt = sum(1 for r in existing.values() if "skip" in r["parse_status"])
fail_cnt = sum(1 for r in existing.values() if r["parse_status"] == "image_scan_no_text_layer")
parse_lines += [
    "",
    f"**成功：** {ok_cnt}  **图像扫描无法解析：** {fail_cnt}  **其他跳过：** {skip_cnt}",
    "",
    "## PDF解析说明",
    "- HLJ-005/HLJ-006：515页/330页大型PDF，仅提取含'大豆'关键词相关页面（129页/99页）",
    "- HLJ-007：12页小型PDF，全文提取（6,147字符）",
    "- HLJ-004：316页图像扫描件PDF，无文本层，无法通过文本提取方式解析；OCR方案不可靠，标注为不可解析",
    "",
    "## 保存路径",
    "- 解析后的纯文本：`knowledge_base/parsed_text/<source_id>.txt`",
    "- 索引文件：`knowledge_base/parsed_text/parsed_text_index.csv`",
]
(PARSED_DIR / "parse_report.md").write_text("\n".join(parse_lines), encoding="utf-8")
print("  parse_report.md updated")

print(f"\n[DONE]")
print(f"  +{new_ev_added} evidence,  +{new_ru_added} rules,  +{new_th_added} thresholds")
print(f"  Total: evidence={len(ev_existing)}, rules={len(rm_existing)}, thresholds={len(rt_existing)}")
print(f"  PDF parse results:")
print(f"    HLJ-004: image scan, no text layer")
print(f"    HLJ-005: ok_partial (129 soybean pages, 76,550 chars)")
print(f"    HLJ-006: ok_partial (99 soybean pages, 65,636 chars)")
print(f"    HLJ-007: ok (12 pages, 6,147 chars)")
