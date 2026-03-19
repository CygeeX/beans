# -*- coding: utf-8 -*-
# =============================================================
# 【文件名称】io_utils.py —— 数据读取与特征构建模块
# 【文件作用】解析用户上传的地面观测压缩包（ground.zip）和产量表，
#             构建结构化特征表，并基于规则生成中文田间管理建议。
#             是整个数据处理层的唯一入口模块。
# 【系统位置】soy_core_v1_project/src/io_utils.py
# 【所属模块】数据处理 / API
# 【答辩说明】答辩时可说明原始数据格式（多期 Excel 观测表）、
#             时序特征摊平构建逻辑，以及基于 SPAD 和株高阈值的
#             规则型管理建议生成机制。
# =============================================================
import re
import zipfile
from io import BytesIO
import os

import numpy as np
import pandas as pd


def _parse_date_from_name(name: str) -> str:
    """
    从文件名中提取日期（尽量鲁棒）：
    - 支持 '7.22.xlsx' / '07-22.xls' / '7_22.xlsx' 等
    返回：'0722' 这种四位字符串
    """
    m = re.search(r"(\d{1,2})[.\-_](\d{1,2})", name)
    if not m:
        return "unknown"
    mm = int(m.group(1))
    dd = int(m.group(2))
    return f"{mm:02d}{dd:02d}"


def read_ground_zip(ground_zip_path: str) -> pd.DataFrame:
    """
    读取 ground.zip 内的所有 Excel，输出长表：
    date, field_id, quadrat, spad_mean, height, pod_height
    """
    rows = []
    with zipfile.ZipFile(ground_zip_path, "r") as z:
        for fn in z.namelist():

            # 1) 过滤常见垃圾/临时文件
            base = os.path.basename(fn)
            if "__MACOSX" in fn or base.startswith("._") or base == ".DS_Store" or base.startswith("~$"):
                continue

            # 2) 只处理 xlsx / xls
            if not fn.lower().endswith((".xlsx", ".xls")):
                continue

            date = _parse_date_from_name(fn)
            data = z.read(fn)

            # 3) ⭐关键：BytesIO 无法自动判断格式，必须指定 engine
            if fn.lower().endswith(".xlsx"):
                df = pd.read_excel(BytesIO(data), engine="openpyxl")
            else:  # .xls
                # 需要安装：pip install xlrd==2.0.1
                df = pd.read_excel(BytesIO(data), engine="xlrd")

            # 统一列名：去掉空格
            df.columns = [str(c).strip() for c in df.columns]

            # 处理合并单元格导致的空值
            if "田块" in df.columns:
                df["田块"] = df["田块"].ffill()
            if "样方" in df.columns:
                df["样方"] = df["样方"].ffill()

            # 计算 SPAD 均值
            spad_cols = [c for c in df.columns if str(c).upper().startswith("SPAD")]
            if len(spad_cols) == 0:
                continue
            df["spad_mean"] = df[spad_cols].mean(axis=1)

            # 高度列（兼容不同写法）
            h_col = None
            for cand in ["总高度(cm)", "总高度（cm）", "总高度", "总高度(cm )"]:
                if cand in df.columns:
                    h_col = cand
                    break
            ph_col = None
            for cand in ["结荚高度(cm)", "结荚高度（cm）", "结荚高度"]:
                if cand in df.columns:
                    ph_col = cand
                    break

            for _, r in df.iterrows():
                field = str(r.get("田块", "")).strip()
                quad = str(r.get("样方", "")).strip()
                if field == "" or field.lower() == "nan":
                    continue
                rows.append({
                    "date": date,
                    "field_id": field,
                    "quadrat": quad,
                    "spad_mean": float(r["spad_mean"]) if pd.notna(r["spad_mean"]) else np.nan,
                    "height": float(r[h_col]) if h_col and pd.notna(r.get(h_col)) else np.nan,
                    "pod_height": float(r[ph_col]) if ph_col and pd.notna(r.get(ph_col)) else np.nan,
                })

    return pd.DataFrame(rows)


def read_yield_xlsx(yield_xlsx_path: str) -> pd.DataFrame:
    """
    兼容两种 yield 输入格式，并统一返回 DataFrame：field_id, yield
    A) 新格式（推荐）：两列：field_id + yield/产量
    B) 旧格式：横向"无人机测产1..15"，某行含"产量"关键字，行内有 15 个数字

    返回：
    - DataFrame: field_id(T1..T15), yield(float)
    """
    # 1) 先尝试两列表格式（带表头）
    try:
        df2 = pd.read_excel(yield_xlsx_path)
    except Exception:
        df2 = None

    if df2 is not None and len(df2.columns) >= 2:
        cols_lower = [str(c).strip().lower() for c in df2.columns]

        def _find_col(candidates):
            for cand in candidates:
                for i, c in enumerate(cols_lower):
                    if cand in c:
                        return df2.columns[i]
            return None

        col_fid = _find_col(["field_id", "field", "plot", "田块"])
        col_y = _find_col(["yield", "产量"])

        if col_fid is not None and col_y is not None:
            tmp = df2[[col_fid, col_y]].copy()
            tmp.columns = ["field_id", "yield"]
            tmp["field_id"] = tmp["field_id"].astype(str).str.strip().str.upper()

            # 只保留 T1..T15
            tmp = tmp[tmp["field_id"].str.match(r"^T\d+$", na=False)].copy()
            tmp["t_num"] = tmp["field_id"].str.extract(r"^T(\d+)$").astype(int)
            tmp = tmp[tmp["t_num"].between(1, 15)].sort_values("t_num")
            tmp["yield"] = pd.to_numeric(tmp["yield"], errors="coerce")
            tmp = tmp.dropna(subset=["yield"])

            # 必须齐全 15 个
            if tmp["t_num"].nunique() == 15:
                tmp = tmp[["field_id", "yield"]].reset_index(drop=True)
                return tmp

    # 2) 兼容旧格式：无表头扫描"产量"行，抽 15 个数字
    df = pd.read_excel(yield_xlsx_path, header=None)
    text = df.astype(str).fillna("")

    keywords = ["产量", "yield"]
    hit_rows = []
    for r in range(text.shape[0]):
        row_join = " ".join(text.iloc[r].tolist()).lower()
        if any(k in row_join for k in keywords):
            hit_rows.append(r)

    def _extract_15_numbers_from_row(ridx: int):
        row = df.iloc[ridx].tolist()
        nums = []
        for cell in row:
            if pd.isna(cell):
                continue
            if isinstance(cell, (int, float)) and np.isfinite(cell):
                nums.append(float(cell))
                continue
            s = str(cell)
            for m in re.findall(r"-?\d+(?:\.\d+)?", s):
                try:
                    nums.append(float(m))
                except Exception:
                    pass
        if len(nums) >= 15:
            return nums[-15:]
        return None

    nums = None
    for r in hit_rows:
        got = _extract_15_numbers_from_row(r)
        if got is not None:
            nums = got
            break

    if nums is None:
        nums_all = []
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                cell = df.iat[r, c]
                if pd.isna(cell):
                    continue
                if isinstance(cell, (int, float)) and np.isfinite(cell):
                    nums_all.append(float(cell))
                else:
                    s = str(cell)
                    for m in re.findall(r"-?\d+(?:\.\d+)?", s):
                        try:
                            nums_all.append(float(m))
                        except Exception:
                            pass
        if len(nums_all) >= 15:
            nums = nums_all[-15:]

    if nums is None or len(nums) != 15:
        raise ValueError(f"未能从 yield.xlsx 中解析出 15 个产量数字（解析到 {0 if nums is None else len(nums)} 个）。")

    out = pd.DataFrame({
        "field_id": [f"T{k}" for k in range(1, 16)],
        "yield": [float(nums[k-1]) for k in range(1, 16)]
    })
    return out


# 特征表构建：仅读取观测数据，生成不含真实产量的特征表（供 /predict 接口使用）
def build_feature_table(ground_zip_path: str) -> pd.DataFrame:
    """
    生成"特征表"（每块田一行），不包含真实产量：
    - 多日期摊平特征
    - 衍生特征：spad_last, height_last, spad_trend, height_trend

    /predict 会用它（因为用户通常没有真实产量）
    """
    g = read_ground_zip(ground_zip_path)

    agg = g.groupby(["date", "field_id"]).agg(
        spad_mean=("spad_mean", "mean"),
        spad_std=("spad_mean", "std"),
        height_mean=("height", "mean"),
        pod_height_mean=("pod_height", "mean"),
    ).reset_index()

    wide = agg.pivot(index="field_id", columns="date")
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    wide = wide.reset_index()

    dates = sorted(agg["date"].unique().tolist())
    last = dates[-1]

    wide["spad_last"] = wide.get(f"spad_mean_{last}")
    wide["height_last"] = wide.get(f"height_mean_{last}")

    def _trend(prefix: str):
        ys = []
        xs = []
        for idx, d in enumerate(dates):
            col = f"{prefix}_{d}"
            if col in wide.columns:
                ys.append(wide[col].values)
                xs.append(idx)
        if len(xs) < 2:
            return np.zeros(len(wide))
        X = np.array(xs, dtype=float)
        Y = np.vstack(ys).T
        Xc = X - X.mean()
        denom = (Xc ** 2).sum()
        slope = (Y @ Xc) / denom
        return slope

    wide["spad_trend"] = _trend("spad_mean")
    wide["height_trend"] = _trend("height_mean")

    return wide


# 训练表构建：读取观测数据并合并真实产量，生成含 yield 列的训练特征表（供 /train 接口使用）
def build_training_table(ground_zip_path: str, yield_xlsx_path: str) -> pd.DataFrame:
    """
    生成训练表（每块田一行）：
    特征表 + 真实产量 yield
    """
    wide = build_feature_table(ground_zip_path)
    y = read_yield_xlsx(yield_xlsx_path)
    return wide.merge(y, on="field_id", how="inner")


# 管理建议生成：基于预测等级和地块 SPAD/株高特征，按规则输出中文田间管理建议
def make_advice_rules(df_train_like: pd.DataFrame, df_pred_cn: pd.DataFrame) -> dict:
    """
    基于预测结果与地块特征生成田间管理建议：
    - 低产 + SPAD偏低（≤批次P30）→ 追肥提示
    - 低产 + 株高增长偏弱（≤批次P30）→ 株高管理提示
    - 低产（其他）→ 通用低产提示
    - 非低产 → 长势正常提示

    返回：{field_id: {"预测产量(kg/100株)": float, "等级": str, "建议": [str, ...]}}
    """
    merged = df_train_like.merge(
        df_pred_cn[["田块", "预测产量(kg/100株)", "等级"]],
        left_on="field_id", right_on="田块", how="left"
    )

    # 批次内分位数阈值
    spad_low = None
    if "spad_last" in merged.columns:
        vals = merged["spad_last"].astype(float).dropna().values
        if len(vals) > 0:
            spad_low = float(np.nanpercentile(vals, 30))

    htrend_low = None
    if "height_mean_slope" in merged.columns:
        vals = merged["height_mean_slope"].astype(float).dropna().values
        if len(vals) > 0:
            htrend_low = float(np.nanpercentile(vals, 30))

    adv = {}
    for _, r in merged.iterrows():
        fid = r["field_id"]
        grade = str(r.get("等级", ""))
        pred_yield = r.get("预测产量(kg/100株)", None)

        tips = []
        if grade == "低产":
            spad = r.get("spad_last", None)
            if spad_low is not None and pd.notna(spad) and float(spad) <= spad_low:
                tips.append("SPAD偏低且预测产量偏低：可能营养/氮素不足，建议复核叶色并评估追肥时机。")

            hslope = r.get("height_mean_slope", None)
            if htrend_low is not None and pd.notna(hslope) and float(hslope) <= htrend_low:
                tips.append("株高增长趋势偏弱：可能生长受限，建议排查水分、密度与病虫害。")

            if not tips:
                tips.append("预测产量偏低：建议重点巡田，结合土壤与病虫害情况进行分区管理。")
        else:
            tips.append("整体长势正常：建议保持常规田间管理，关注后期水肥与病虫害。")

        adv[fid] = {
            "预测产量(kg/100株)": float(pred_yield) if pd.notna(pred_yield) else None,
            "等级": grade,
            "建议": tips[:2],
        }

    return adv
