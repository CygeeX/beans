# -*- coding: utf-8 -*-
"""
大豆规则知识库下载与目录构建脚本
生成完整目录结构、下载所有来源文件、构建元数据 CSV
"""
import sys, os, csv, time, sqlite3, traceback
sys.stdout.reconfigure(encoding='utf-8')

import requests
from datetime import datetime
from pathlib import Path

# ── 根目录 ─────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent / "knowledge_base"
DIRS = {
    "hlj":       ROOT / "raw_sources" / "hlj",
    "moa":       ROOT / "raw_sources" / "moa",
    "extension": ROOT / "raw_sources" / "extension",
    "fao":       ROOT / "raw_sources" / "fao",
}
for d in [ROOT, ROOT / "raw_sources"] + list(DIRS.values()):
    d.mkdir(parents=True, exist_ok=True)

# ── 下载清单定义 ─────────────────────────────────────────────
SOURCES = [
    # ─── hlj ───────────────────────────────────────────────
    {
        "source_id": "HLJ-001",
        "file_name": "2026_黑龙江备春耕大豆生产技术指导意见.html",
        "source_title": "2026年黑龙江备春耕大豆生产技术指导意见",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2026-03",
        "source_type": "html",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115393/202603/c00_31919966.shtml",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-002",
        "file_name": "2025_黑龙江主要粮食作物科学施肥技术指导意见.html",
        "source_title": "2025年黑龙江主要粮食作物科学施肥技术指导意见",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2025-03",
        "source_type": "html",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115385/202503/c00_31821370.shtml",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-003",
        "file_name": "2026_黑龙江农作物主要病虫草鼠害防控指导意见.html",
        "source_title": "2026年黑龙江农作物主要病虫草鼠害防控指导意见",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2026-02",
        "source_type": "html",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115423/202602/c00_31911356.shtml",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-004",
        "file_name": "2026_黑龙江农作物主要病虫草鼠害防控指导意见.pdf",
        "source_title": "2026年黑龙江省农作物主要病虫草鼠害防控指导意见（PDF附件）",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2026-02",
        "source_type": "pdf",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115423/202602/31911356/files/%E5%85%B3%E4%BA%8E%E5%8D%B0%E5%8F%91%E3%80%8A2026%E5%B9%B4%E9%BB%91%E9%BE%99%E6%B1%9F%E7%9C%81%E5%86%9C%E4%BD%9C%E7%89%A9%E4%B8%BB%E8%A6%81%E7%97%85%E8%99%AB%E8%8D%89%E9%BC%A0%E5%AE%B3%E9%98%B2%E6%8E%A7%E6%8C%87%E5%AF%BC%E6%84%8F%E8%A7%81%E3%80%8B%E7%9A%84%E9%80%9A%E7%9F%A5.pdf",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-005",
        "file_name": "2025_黑龙江农业主推技术.pdf",
        "source_title": "2025年黑龙江省农业主推技术",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2025-03",
        "source_type": "pdf",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115423/202503/31825925/files/2025%E5%B9%B4%E9%BB%91%E9%BE%99%E6%B1%9F%E7%9C%81%E5%86%9C%E4%B8%9A%E4%B8%BB%E6%8E%A8%E6%8A%80%E6%9C%AF.pdf",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-006",
        "file_name": "2025_黑龙江农作物栽培技术模式汇编.pdf",
        "source_title": "2025年黑龙江省农作物栽培技术模式汇编",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2025-02",
        "source_type": "pdf",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115423/202502/31810960/files/2025%E5%B9%B4%E9%BB%91%E9%BE%99%E6%B1%9F%E7%9C%81%E5%86%9C%E4%BD%9C%E7%89%A9%E6%A0%BD%E5%9F%B9%E6%8A%80%E6%9C%AF%E6%A8%A1%E5%BC%8F%E6%B1%87%E7%BC%96.pdf",
        "subdir": "hlj",
    },
    {
        "source_id": "HLJ-007",
        "file_name": "2025_黑龙江科学施肥增效项目实施方案.pdf",
        "source_title": "黑龙江省2025年科学施肥增效项目实施方案",
        "publisher": "黑龙江省农业农村厅",
        "publish_date": "2025-11",
        "source_type": "pdf",
        "region_scope": "黑龙江省",
        "source_url": "https://nynct.hlj.gov.cn/nynct/c115423/202511/31890865/files/%E9%99%84%E4%BB%B61.%E9%BB%91%E9%BE%99%E6%B1%9F%E7%9C%812025%E5%B9%B4%E7%A7%91%E5%AD%A6%E6%96%BD%E8%82%A5%E5%A2%9E%E6%95%88%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%96%BD%E6%96%B9%E6%A1%88.pdf",
        "subdir": "hlj",
    },
    # ─── moa ───────────────────────────────────────────────
    {
        "source_id": "MOA-001",
        "file_name": "大豆根瘤菌接种及配套施肥技术指导意见.html",
        "source_title": "大豆根瘤菌接种及配套施肥技术指导意见",
        "publisher": "农业农村部",
        "publish_date": "2022-01",
        "source_type": "html",
        "region_scope": "全国",
        "source_url": "https://www.moa.gov.cn/gk/nszd_1/2021/202201/t20220120_6387235.htm",
        "subdir": "moa",
    },
    {
        "source_id": "MOA-002",
        "file_name": "农事指导_索引页.html",
        "source_title": "农业农村部农事指导索引（第11页）",
        "publisher": "农业农村部",
        "publish_date": "ongoing",
        "source_type": "html",
        "region_scope": "全国",
        "source_url": "https://www.moa.gov.cn/gk/nszd_1/index_11.htm",
        "subdir": "moa",
    },
    # ─── extension ─────────────────────────────────────────
    {
        "source_id": "EXT-001",
        "file_name": "iowa_soybean_fertilization.html",
        "source_title": "Nutrient Requirements of Soybean (Iowa State Extension)",
        "publisher": "Iowa State University Extension",
        "publish_date": "ongoing",
        "source_type": "html",
        "region_scope": "USA/Iowa",
        "source_url": "https://crops.extension.iastate.edu/encyclopedia/nutrient-requirements-soybean",
        "subdir": "extension",
    },
    {
        "source_id": "EXT-002",
        "file_name": "umn_soybean_growth_stages.html",
        "source_title": "Soybean Growth Stages (University of Minnesota Extension)",
        "publisher": "University of Minnesota Extension",
        "publish_date": "ongoing",
        "source_type": "html",
        "region_scope": "USA/Minnesota",
        "source_url": "https://extension.umn.edu/growing-soybean/soybean-growth-stages",
        "subdir": "extension",
    },
    # ─── fao ───────────────────────────────────────────────
    {
        "source_id": "FAO-001",
        "file_name": "fao_soybean_water_management.html",
        "source_title": "FAO Soybean Crop Information (Water Management)",
        "publisher": "FAO",
        "publish_date": "ongoing",
        "source_type": "html",
        "region_scope": "Global",
        "source_url": "https://www.fao.org/land-water/databases-and-software/crop-information/soybean/en/",
        "subdir": "fao",
    },
]

# ── 请求头（模拟浏览器，避免 403）─────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.9",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
TIMEOUT = 30

# ── 下载函数 ──────────────────────────────────────────────────
def download_file(url, local_path):
    """下载单个文件，返回 (success, size_bytes, error_msg)"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                            allow_redirects=True, verify=True)
        if resp.status_code == 200:
            content = resp.content
            if len(content) < 100:
                return False, len(content), f"响应内容过短（{len(content)} bytes），可能为空页"
            with open(local_path, "wb") as f:
                f.write(content)
            return True, len(content), ""
        else:
            return False, 0, f"HTTP {resp.status_code}"
    except requests.exceptions.SSLError as e:
        # SSL 失败时尝试不验证
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                                allow_redirects=True, verify=False)
            if resp.status_code == 200:
                content = resp.content
                with open(local_path, "wb") as f:
                    f.write(content)
                return True, len(content), "SSL验证跳过（自签名证书）"
            else:
                return False, 0, f"SSL跳过后 HTTP {resp.status_code}"
        except Exception as e2:
            return False, 0, f"SSL错误后重试失败: {str(e2)[:120]}"
    except requests.exceptions.Timeout:
        return False, 0, f"超时（{TIMEOUT}s）"
    except requests.exceptions.ConnectionError as e:
        return False, 0, f"连接失败: {str(e)[:120]}"
    except Exception as e:
        return False, 0, f"未知错误: {str(e)[:120]}"

# ── 主下载循环 ────────────────────────────────────────────────
print("=" * 70)
print("  大豆规则知识库 · 文件下载")
print(f"  时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

manifest_rows = []
for i, src in enumerate(SOURCES, 1):
    local_path = DIRS[src["subdir"]] / src["file_name"]
    print(f"\n[{i:02d}/{len(SOURCES)}] {src['source_id']} — {src['file_name']}")
    print(f"        URL: {src['source_url'][:80]}...")

    t0 = time.time()
    success, size, err = download_file(src["source_url"], local_path)
    elapsed = time.time() - t0

    status = "success" if success else "failed"
    print(f"        状态: {status.upper()}  大小: {size:,} bytes  耗时: {elapsed:.1f}s")
    if not success:
        print(f"        原因: {err}")

    # 若失败则写一个占位 txt（不影响目录结构）
    if not success:
        placeholder = local_path.with_suffix(local_path.suffix + ".failed.txt")
        placeholder.write_text(
            f"DOWNLOAD FAILED\nURL: {src['source_url']}\nError: {err}\nTime: {datetime.now().isoformat()}\n",
            encoding="utf-8"
        )

    manifest_rows.append({
        "source_id": src["source_id"],
        "file_name": src["file_name"],
        "source_title": src.get("source_title", ""),
        "publisher": src.get("publisher", ""),
        "publish_date": src.get("publish_date", ""),
        "source_type": src.get("source_type", ""),
        "region_scope": src.get("region_scope", ""),
        "source_url": src["source_url"],
        "local_path": str(local_path.relative_to(ROOT.parent)),
        "download_status": status,
        "file_size_bytes": size,
        "download_time_sec": round(elapsed, 1),
        "error_message": err,
        "downloaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    time.sleep(0.8)   # 礼貌延迟

# ── 写出 source_master.csv ─────────────────────────────────
sm_path = ROOT / "source_master.csv"
sm_fields = ["source_id","file_name","source_title","publisher","publish_date",
             "source_type","region_scope","source_url","local_path","download_status"]
with open(sm_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sm_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(manifest_rows)
print(f"\n✅ source_master.csv 已写出：{sm_path}")

# ── 写出 download_manifest.csv ─────────────────────────────
dm_path = ROOT / "download_manifest.csv"
dm_fields = ["source_id","file_name","source_url","local_path","download_status",
             "file_size_bytes","download_time_sec","error_message","downloaded_at"]
with open(dm_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dm_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(manifest_rows)
print(f"✅ download_manifest.csv 已写出：{dm_path}")

# ── 创建空骨架 CSV（evidence_master / rule_master / rule_threshold）
for fname, fields in [
    ("evidence_master.csv",  ["evidence_id","source_id","page_or_section","quote_cn",
                               "quote_en","crop","topic","metric","value","unit","confidence","notes"]),
    ("rule_master.csv",      ["rule_id","rule_cn","rule_en","category","crop",
                               "growth_stage","condition","action","evidence_ids","confidence","notes"]),
    ("rule_threshold.csv",   ["threshold_id","rule_id","metric","comparator","value","unit",
                               "value_source","evidence_ids","notes"]),
]:
    p = ROOT / fname
    if not p.exists():
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerow(fields)
        print(f"✅ {fname} 骨架已创建")

# ── 创建 SQLite 知识库 ─────────────────────────────────────
db_path = ROOT / "kb.sqlite"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    file_name TEXT,
    source_title TEXT,
    publisher TEXT,
    publish_date TEXT,
    source_type TEXT,
    region_scope TEXT,
    source_url TEXT,
    local_path TEXT,
    download_status TEXT,
    file_size_bytes INTEGER,
    downloaded_at TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    source_id TEXT,
    page_or_section TEXT,
    quote_cn TEXT,
    quote_en TEXT,
    crop TEXT,
    topic TEXT,
    metric TEXT,
    value REAL,
    unit TEXT,
    confidence TEXT,
    notes TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    rule_cn TEXT,
    rule_en TEXT,
    category TEXT,
    crop TEXT,
    growth_stage TEXT,
    condition TEXT,
    action TEXT,
    evidence_ids TEXT,
    confidence TEXT,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS thresholds (
    threshold_id TEXT PRIMARY KEY,
    rule_id TEXT,
    metric TEXT,
    comparator TEXT,
    value REAL,
    unit TEXT,
    value_source TEXT,
    evidence_ids TEXT,
    notes TEXT,
    FOREIGN KEY (rule_id) REFERENCES rules(rule_id)
);
""")
for row in manifest_rows:
    cur.execute("""
        INSERT OR REPLACE INTO sources
        (source_id, file_name, source_title, publisher, publish_date,
         source_type, region_scope, source_url, local_path, download_status,
         file_size_bytes, downloaded_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (row["source_id"], row["file_name"], row["source_title"],
          row["publisher"], row["publish_date"], row["source_type"],
          row["region_scope"], row["source_url"], row["local_path"],
          row["download_status"], row["file_size_bytes"], row["downloaded_at"]))
conn.commit()
conn.close()
print(f"✅ kb.sqlite 已创建（{db_path}）")

# ── 统计汇总 ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  下载汇总报告")
print("=" * 70)
success_rows = [r for r in manifest_rows if r["download_status"] == "success"]
failed_rows  = [r for r in manifest_rows if r["download_status"] == "failed"]
html_rows = [r for r in success_rows if r["source_type"] == "html"]
pdf_rows  = [r for r in success_rows if r["source_type"] == "pdf"]

print(f"\n  总计：{len(manifest_rows)} 个文件")
print(f"  ✅ 成功：{len(success_rows)} 个（HTML: {len(html_rows)}，PDF: {len(pdf_rows)}）")
print(f"  ❌ 失败：{len(failed_rows)} 个")

if success_rows:
    print("\n  成功下载的文件：")
    for r in success_rows:
        tag = "[HTML]" if r["source_type"] == "html" else "[PDF] "
        size_kb = r["file_size_bytes"] // 1024
        print(f"    {tag}  {r['source_id']:8s}  {r['file_name'][:55]}  ({size_kb} KB)")

if failed_rows:
    print("\n  下载失败的文件：")
    for r in failed_rows:
        print(f"    ❌  {r['source_id']:8s}  {r['file_name'][:50]}")
        print(f"          原因：{r['error_message'][:80]}")

# ── 文件非空检查 ──────────────────────────────────────────────
print("\n  文件非空校验：")
for r in success_rows:
    p = ROOT.parent / r["local_path"]
    actual_size = p.stat().st_size if p.exists() else 0
    ok = "✓" if actual_size > 0 else "✗ (空文件!)"
    print(f"    {ok}  {r['source_id']:8s}  {r['file_name'][:50]}  {actual_size:,} bytes")

# ── 目录树 ────────────────────────────────────────────────────
print("\n  目录树（knowledge_base/）：")
for p in sorted(ROOT.rglob("*")):
    level = len(p.relative_to(ROOT).parts)
    indent = "  " * level
    if p.is_dir():
        print(f"    {indent}{p.name}/")
    else:
        size = p.stat().st_size
        print(f"    {indent}{p.name}  ({size:,} B)")

print("\n" + "=" * 70)
print("  完成！知识库目录已就绪。")
print("=" * 70)
