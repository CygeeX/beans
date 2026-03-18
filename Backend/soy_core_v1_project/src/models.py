# -*- coding: utf-8 -*-
# =============================================================
# 【文件名称】models.py —— 模型核心：特征工程 + 训练 + 推理
# 【文件作用】实现路线A强压缩特征变换、LOOCV 多模型评估与选型、
#             最优模型全量训练、模型序列化存取及推理调用。
#             是系统精度的核心实现文件。
# 【系统位置】soy_core_v1_project/src/models.py
# 【所属模块】模型精度 / 推理
# 【答辩说明】可重点介绍以下三点：
#             1. 路线A特征压缩：将多期时序观测数据压缩为约35维高密度特征；
#             2. 防塌缩 objective：在 LOOCV 中加入软惩罚项，
#                防止模型将所有样本均预测为均值；
#             3. 多模型对比：Ridge / KRR / GPR / SVR / ExtraTrees
#                在严格 LOOCV（n=15）条件下自动选出最优模型。
# =============================================================
"""
小样本 n≈15：RMSE优先 + 路线A(强压缩特征) + 路线B(软惩罚+稳健objective)

路线A（强压缩）：
- 只输出“高密度特征”（窗口均值/变化量/趋势/比值/交互），丢掉原始“日期_变量_stat”列
- 目的：减少共线与噪声，避免 select_k=all 的高维碰巧拟合

路线B（稳健选择）：
objective = RMSE + 0.30*MAE + 0.20*|bias| + λ*max(0, std_thr - std_pred)

候选模型：
- Ridge / KRR(RBF) / GPR / SVR(RBF) / ExtraTrees(对照)
"""

import re
import numpy as np
import pandas as pd

from sklearn.model_selection import LeaveOneOut, ParameterGrid
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor

from sklearn.svm import SVR
from sklearn.kernel_ridge import KernelRidge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel as C
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge

from joblib import dump, load


# ============================================================
# 路线A：强压缩特征工程（建议 n≈15 必开）
# ============================================================
# 路线A强压缩特征工程：将多期时序观测数据压缩为约35维高密度特征，减少共线与过拟合
def transform_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    强压缩版特征工程（适合 n≈15）：
    - 仅保留高密度特征（10~30个量级），丢掉原始“日期_变量_stat”列，减少共线与过拟合。
    - 默认只针对常见变量：SPAD_avg / 总高度(cm) / 结荚高度(cm)；若不存在则对所有变量执行。

    输入：build_training_table / build_feature_table 的输出（含 field_id，train 时含 yield）
    输出：压缩后的特征表（仍含 field_id / yield(若有)）
    """
    keep = ["field_id"]
    if "yield" in df.columns:
        keep.append("yield")

    # 识别形如：spad_mean_0722 / height_mean_0722 / pod_height_mean_0722
    pat = re.compile(r"^(.+?)_(mean|std|min|max)_(\d{4})$")
    meta = []  # (col, date_str, var, stat)
    for c in df.columns:
        m = pat.match(str(c))
        if m:
            meta.append((c, m.group(3), m.group(1), m.group(2)))

    if not meta:
        # 已经不是“原始日期列”结构，直接返回
        return df.copy()

    dates = sorted({d for _, d, _, _ in meta})
    vars_ = sorted({v for _, _, v, _ in meta})

    def get_colname(d, var, stat):
        name = f"{var}_{stat}_{d}"
        return name if name in df.columns else None

    # 优先关键变量；没有就退化为全部变量
    key_vars = [v for v in vars_ if v in ("spad", "height", "pod_height")]
    if not key_vars:
        key_vars = vars_

    out = df[keep].copy()

    # 窗口划分：早/中/晚（按日期排序三段）
    n = len(dates)
    if n <= 2:
        early_idx = list(range(n))
        mid_idx = []
        late_idx = list(range(n))
    else:
        a = max(1, n // 3)
        b = max(1, (n - a) // 2)
        early_idx = list(range(0, a))
        mid_idx = list(range(a, a + b))
        late_idx = list(range(a + b, n)) or [n - 1]

    x = np.arange(n, dtype=float)

    def series_matrix(var, stat):
        cols = [get_colname(d, var, stat) for d in dates]
        if any(c is None for c in cols):
            return None
        return df[cols].to_numpy(dtype=float)

    def first_last(mat):
        first = np.full((mat.shape[0],), np.nan, dtype=float)
        last = np.full((mat.shape[0],), np.nan, dtype=float)
        for i in range(mat.shape[0]):
            row = mat[i]
            idx = np.where(~np.isnan(row))[0]
            if idx.size:
                first[i] = row[idx[0]]
                last[i] = row[idx[-1]]
        return first, last

    def slope_of(mat):
        s = np.full((mat.shape[0],), np.nan, dtype=float)
        for i in range(mat.shape[0]):
            yv = mat[i]
            ok = ~np.isnan(yv)
            if ok.sum() >= 2:
                xi = x[ok]
                yi = yv[ok]
                cov = np.cov(xi, yi, ddof=0)[0, 1]
                varx = np.var(xi)
                s[i] = cov / varx if varx > 0 else 0.0
        return s

    def win_mean(mat, idxs):
        if not idxs:
            return np.full((mat.shape[0],), np.nan, dtype=float)
        return np.nanmean(mat[:, idxs], axis=1)

    # 对每个变量提取高密度特征
    for var in key_vars:
        mat_mean = series_matrix(var, "mean")
        if mat_mean is None:
            continue

        out[f"{var}_mean_all"] = np.nanmean(mat_mean, axis=1)
        out[f"{var}_mean_range"] = np.nanmax(mat_mean, axis=1) - np.nanmin(mat_mean, axis=1)

        f, l = first_last(mat_mean)
        out[f"{var}_mean_last_minus_first"] = l - f
        out[f"{var}_mean_slope"] = slope_of(mat_mean)

        e = win_mean(mat_mean, early_idx)
        m = win_mean(mat_mean, mid_idx)
        t = win_mean(mat_mean, late_idx)
        out[f"{var}_mean_early"] = e
        out[f"{var}_mean_mid"] = m
        out[f"{var}_mean_late"] = t
        out[f"{var}_mean_late_minus_early"] = t - e

        # std 摘要（只留两个，避免维度膨胀）
        mat_std = series_matrix(var, "std")
        if mat_std is not None:
            out[f"{var}_std_all"] = np.nanmean(mat_std, axis=1)
            out[f"{var}_std_range"] = np.nanmax(mat_std, axis=1) - np.nanmin(mat_std, axis=1)

    # 结构比值：pod_height / height（mean）摘要
    if ("height" in vars_) and ("pod_height" in vars_):
        h = series_matrix("height", "mean")
        p = series_matrix("pod_height", "mean")
        if h is not None and p is not None:
            ratio = p / h
            out["pod_ratio_all"] = np.nanmean(ratio, axis=1)
            out["pod_ratio_range"] = np.nanmax(ratio, axis=1) - np.nanmin(ratio, axis=1)
            f, l = first_last(ratio)
            out["pod_ratio_last_minus_first"] = l - f
            out["pod_ratio_late_minus_early"] = win_mean(ratio, late_idx) - win_mean(ratio, early_idx)

    # 交互耦合：SPAD×高度、SPAD×占比（all & late-early）
    def arr(name):
        return out[name].to_numpy(dtype=float) if name in out.columns else None

    sp_all = arr("spad_mean_all")
    sp_le = arr("spad_mean_late_minus_early")
    h_all = arr("height_mean_all")
    h_le = arr("height_mean_late_minus_early")
    r_all = arr("pod_ratio_all")
    r_le = arr("pod_ratio_late_minus_early")

    if sp_all is not None and h_all is not None:
        out["交互_SPADx高度_all"] = sp_all * h_all
    if sp_le is not None and h_le is not None:
        out["交互_SPADx高度_late_minus_early"] = sp_le * h_le
    if sp_all is not None and r_all is not None:
        out["交互_SPADx占比_all"] = sp_all * r_all
    if sp_le is not None and r_le is not None:
        out["交互_SPADx占比_late_minus_early"] = sp_le * r_le

    # 清理 inf
    num_cols = [c for c in out.columns if c not in ("field_id", "yield")]
    out[num_cols] = out[num_cols].replace([np.inf, -np.inf], np.nan)

    # 兼容性别名：make_advice_rules() 需要 spad_last
    if "spad_mean_late" in out.columns and "spad_last" not in out.columns:
        out["spad_last"] = out["spad_mean_late"]
    # 注：height_mean_slope 即为株高趋势，make_advice_rules() 已改为自动回退，无需重复添加 height_trend

    return out


# ============================================================
# ✅ 双保险：自动接入路线A（防止绕过pipeline直接传原始表）
# ============================================================
_DATE_COL_RE = re.compile(r"^(.+?)_(mean|std|min|max)_(\d{4})$")


def _has_raw_date_columns(df: pd.DataFrame) -> bool:
    for c in df.columns:
        if _DATE_COL_RE.match(str(c)):
            return True
    return False


def _auto_transform_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    # 如果仍然含“日期_变量_stat”列，说明还没压缩，自动压缩一次
    return transform_feature_table(df) if _has_raw_date_columns(df) else df


# ============================================================
# Helpers
# ============================================================
def _feature_cols(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in ["field_id", "yield"]]


def _score(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    return {"MAE": mae, "RMSE": rmse, "R2": r2}


def _loocv_predict(model, X: np.ndarray, y: np.ndarray) -> np.ndarray:
    loo = LeaveOneOut()
    pred = np.zeros(len(y), dtype=float)
    for tr, te in loo.split(X):
        model.fit(X[tr], y[tr])
        pred[te[0]] = float(model.predict(X[te])[0])
    return pred


def _std_threshold(y: np.ndarray, min_ratio: float = 0.18, floor: float = 0.04) -> float:
    return max(floor, min_ratio * float(np.std(y)))


def _wrap_target(reg):
    return TransformedTargetRegressor(regressor=reg, transformer=StandardScaler())


# ============================================================
# Candidates
# ============================================================
def _build_candidates(random_state: int = 42):
    candidates = []

    ridge = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", Ridge())
    ])
    candidates.append(("Ridge", ridge, {"model__alpha": [0.01, 0.1, 0.3, 1, 3, 10, 30, 100]}))

    krr = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select", SelectKBest(score_func=f_regression, k=8)),
        ("scaler", StandardScaler()),
        ("model", _wrap_target(KernelRidge(kernel="rbf")))
    ])
    candidates.append(("KRR_RBF", krr, {
        "select__k": [4, 6, 8, 10, 12, "all"],
        "model__regressor__alpha": [1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3, 1.0],
        "model__regressor__gamma": [0.03, 0.06, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2],
    }))

    gpr_kernel = C(1.0, (1e-2, 1e2)) * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e2)) + \
                 WhiteKernel(noise_level=1e-2, noise_level_bounds=(1e-6, 1e0))
    gpr = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select", SelectKBest(score_func=f_regression, k=8)),
        ("scaler", StandardScaler()),
        ("model", _wrap_target(GaussianProcessRegressor(
            kernel=gpr_kernel,
            normalize_y=False,
            random_state=random_state
        )))
    ])
    candidates.append(("GPR", gpr, {
        "select__k": [4, 6, 8, 10, 12, "all"],
        "model__regressor__alpha": [1e-6, 1e-5, 1e-4],
    }))

    svr = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select", SelectKBest(score_func=f_regression, k=8)),
        ("scaler", StandardScaler()),
        ("model", _wrap_target(SVR(kernel="rbf")))
    ])
    candidates.append(("SVR_RBF", svr, {
        "select__k": [4, 6, 8, 10, 12, "all"],
        "model__regressor__C": [1, 3, 10, 30, 60],
        "model__regressor__gamma": [0.03, 0.06, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2],
        "model__regressor__epsilon": [0.01, 0.02, 0.04, 0.06, 0.08],
    }))

    et = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", ExtraTreesRegressor(
            n_estimators=400, random_state=random_state, n_jobs=-1, bootstrap=False
        ))
    ])
    candidates.append(("ExtraTrees", et, {
        "model__min_samples_leaf": [1, 2, 3, 4],
        "model__min_samples_split": [2, 4, 6],
        "model__max_depth": [None, 3, 5],
        "model__max_features": ["sqrt", 0.7, 1.0],
    }))

    return candidates


# ============================================================
# 路线B：软惩罚 + 稳健objective 的 LOOCV 搜索
# ============================================================
def _search_best_model_loocv(
    X: np.ndarray,
    y: np.ndarray,
    random_state: int = 42,
    min_std_ratio: float = 0.18,
    min_std_floor: float = 0.04,
    collapse_lambda: float = 1.2,
):
    candidates = _build_candidates(random_state=random_state)
    std_thr = _std_threshold(y, min_ratio=min_std_ratio, floor=min_std_floor)

    best = None
    all_results = []

    for model_name, base_model, grid in candidates:
        for params in ParameterGrid(grid):
            model = base_model
            model.set_params(**params)

            y_pred = _loocv_predict(model, X, y)
            sc = _score(y, y_pred)
            std_pred = float(np.std(y_pred))

            penalty = max(0.0, std_thr - std_pred)
            bias = float(np.mean(y_pred) - np.mean(y))

            obj = float(
                sc["RMSE"]
                + 0.30 * sc["MAE"]
                + 0.20 * abs(bias)
                + collapse_lambda * penalty
            )

            rec = {
                "model": model_name,
                "params": params,
                **sc,
                "std_pred": std_pred,
                "min_pred": float(np.min(y_pred)),
                "max_pred": float(np.max(y_pred)),
                "std_threshold": float(std_thr),
                "penalty": float(penalty),
                "bias": float(bias),
                "objective": obj,
            }
            all_results.append(rec)

            key = (obj, sc["RMSE"], sc["MAE"])
            if best is None or key < best["key"]:
                best = {
                    "key": key,
                    "model": model_name,
                    "params": params,
                    "y_pred": y_pred,
                    "metrics": sc,
                    "std_pred": std_pred,
                    "min_pred": rec["min_pred"],
                    "max_pred": rec["max_pred"],
                    "objective": obj,
                    "std_threshold": float(std_thr),
                    "lambda": float(collapse_lambda),
                    "bias": float(bias),
                }

    best_name = best["model"]
    best_params = best["params"]

    best_template = None
    for name, base_model, _ in candidates:
        if name == best_name:
            best_template = base_model
            break
    best_template.set_params(**best_params)

    return best_name, best_params, best_template, best["y_pred"], all_results, {
        "std_threshold_used": best["std_threshold"],
        "collapse_lambda": best["lambda"],
        "objective": best["objective"],
        "bias": best["bias"],
    }


# ============================================================
# Public API
# ============================================================
# LOOCV 评估入口：对五种候选模型做留一法交叉验证，用软惩罚 objective 选出最优模型
def loocv_train_predict(df: pd.DataFrame):
    # ✅ 双保险：防止外部直接传原始表（未压缩）
    df = _auto_transform_if_needed(df)

    y = df["yield"].values.astype(float)
    feat_cols = _feature_cols(df)
    X = df[feat_cols].values

    best_name, best_params, _, y_pred, all_results, extra = _search_best_model_loocv(
        X, y,
        random_state=42,
        min_std_ratio=0.18,
        min_std_floor=0.04,
        collapse_lambda=1.2,
    )

    sc_best = _score(y, y_pred)

    order = np.argsort(-y_pred)
    level = np.array(["中产"] * len(df), dtype=object)
    k = min(5, max(1, len(df) // 3))
    level[order[:k]] = "高产"
    level[order[-k:]] = "低产"

    df_pred = pd.DataFrame({
        "田块": df["field_id"].values,
        "真实产量(kg/100株)": y,
        "预测产量(kg/100株)": y_pred,
        "等级": level
    })

    model_best = {}
    for rec in all_results:
        m = rec["model"]
        key = (rec["objective"], rec["RMSE"], rec["MAE"])
        if m not in model_best or key < model_best[m]["key"]:
            model_best[m] = {
                "key": key,
                "MAE": rec["MAE"],
                "RMSE": rec["RMSE"],
                "R2": rec["R2"],
                "std_pred": rec["std_pred"],
                "min_pred": rec["min_pred"],
                "max_pred": rec["max_pred"],
                "objective": rec["objective"],
                "penalty": rec["penalty"],
                "bias": rec["bias"],
                "params": rec["params"],
            }

    metrics = {
        "最优模型": best_name,
        "最优参数": best_params,
        "平均绝对误差MAE": float(sc_best["MAE"]),
        "均方根误差RMSE": float(sc_best["RMSE"]),
        "决定系数R2": float(sc_best["R2"]),
        "预测值标准差std_pred": float(np.std(y_pred)),
        "预测值范围minmax": [float(np.min(y_pred)), float(np.max(y_pred))],
        "防塌缩阈值std_threshold": float(extra["std_threshold_used"]),
        "软惩罚lambda": float(extra["collapse_lambda"]),
        "本次最优objective": float(extra["objective"]),
        "均值偏差bias": float(extra["bias"]),
        "模型对比(各模型最优)": {
            m: {
                "MAE": v["MAE"],
                "RMSE": v["RMSE"],
                "R2": v["R2"],
                "std_pred": v["std_pred"],
                "minmax": [v["min_pred"], v["max_pred"]],
                "objective": v["objective"],
                "penalty": v["penalty"],
                "bias": v["bias"],
                "params": v["params"],
            }
            for m, v in model_best.items()
        }
    }

    return df_pred, metrics


# 全量训练：用最优模型名称和参数在全量15个样本上重新训练，生成可序列化的 bundle
def fit_full_model(df_train: pd.DataFrame, best_model_name: str = None, best_params: dict = None) -> dict:
    # ✅ 双保险：防止外部直接传原始表（未压缩）
    df_train = _auto_transform_if_needed(df_train)

    feat_cols = _feature_cols(df_train)
    X = df_train[feat_cols].values
    y = df_train["yield"].values.astype(float)

    if best_model_name is None or best_params is None:
        _, metrics = loocv_train_predict(df_train)
        best_model_name = metrics["最优模型"]
        best_params = metrics["最优参数"]

    candidates = _build_candidates(random_state=42)
    template = None
    for name, base_model, _ in candidates:
        if name == best_model_name:
            template = base_model
            break
    if template is None:
        raise ValueError(f"Unknown model name: {best_model_name}")

    template.set_params(**best_params)
    template.fit(X, y)

    return {
        "feature_cols": feat_cols,
        "model_name": best_model_name,
        "params": best_params,
        "model": template
    }


# 模型保存：用 joblib 将训练好的 bundle（含特征列名和模型对象）序列化到指定路径
def save_model(bundle: dict, model_path: str) -> None:
    dump(bundle, model_path)


# 模型加载：从指定路径反序列化 bundle（含特征列名、模型名称和已训练的 sklearn Pipeline）
def load_model(model_path: str) -> dict:
    return load(model_path)


# 模型推理：自动补齐缺失特征列为 NaN，确保训练与预测特征对齐后调用模型完成预测
def predict_with_model(bundle: dict, df_feat: pd.DataFrame) -> np.ndarray:
    feat_cols = bundle["feature_cols"]

    Xdf = df_feat.copy()
    for c in feat_cols:
        if c not in Xdf.columns:
            Xdf[c] = np.nan

    X = Xdf[feat_cols].values
    y_pred = bundle["model"].predict(X)
    return np.asarray(y_pred, dtype=float)


# 构建预测结果表：将预测值整理为中文列名 DataFrame，并按数值划分高/中/低产等级
def make_pred_dataframe(df_feat: pd.DataFrame, y_pred: np.ndarray) -> pd.DataFrame:
    df_out = pd.DataFrame({
        "田块": df_feat["field_id"].values,
        "预测产量(kg/100株)": y_pred
    })

    n = len(df_out)
    top_k = min(5, max(1, n // 3))
    bot_k = min(5, max(1, n // 3))

    tmp = df_out.sort_values("预测产量(kg/100株)", ascending=False).reset_index(drop=True)
    level = np.array(["中产"] * n, dtype=object)
    level[:top_k] = "高产"
    level[-bot_k:] = "低产"
    tmp["等级"] = level
    return tmp