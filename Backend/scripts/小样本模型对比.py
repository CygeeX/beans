# -*- coding: utf-8 -*-
"""
小样本友好模型对比（LOOCV）——在去冗余 35 维特征上比较：
SVR_RBF / PLSRegression / BayesianRidge / ARDRegression / GPR / Ridge
使用与 models.py 完全相同的 objective 函数
"""
import sys, os, json, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'soy_core_v1_project'))
sys.path.insert(0, PROJECT_ROOT)

INPUT_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'inputs_best_accuracy'))
OUT_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', '模型对比_去重样本'))
os.makedirs(OUT_DIR, exist_ok=True)

GROUND_ZIP = os.path.join(INPUT_DIR, 'ground_clean_domaincap.zip')
YIELD_XLSX = os.path.join(INPUT_DIR, 'yield_clean.xlsx')

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.svm import SVR
from sklearn.linear_model import Ridge, BayesianRidge, ARDRegression
from sklearn.cross_decomposition import PLSRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel as C
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.base import clone

# ── 构建去冗余特征表 ────────────────────────────────────
from src.io_utils import build_training_table
from src.models import transform_feature_table

print("构建特征表...")
df_raw = build_training_table(GROUND_ZIP, YIELD_XLSX)
df_tx  = transform_feature_table(df_raw)

# 去除 height_trend（若仍存在）
feature_cols = [c for c in df_tx.columns if c not in ('field_id', 'yield', 'height_trend')]
X_all = df_tx[feature_cols].values.astype(float)
y_all = df_tx['yield'].values.astype(float)
fields = df_tx['field_id'].values

print(f"特征数: {len(feature_cols)} （height_trend={'已移除' if 'height_trend' not in feature_cols else '存在'}）")
print(f"样本数: {len(y_all)}")
print()

# ── objective 函数（与 models.py 完全相同）─────────────
LAM = 1.2
MIN_STD_RATIO = 0.18
MIN_STD_FLOOR = 0.04
std_threshold = max(MIN_STD_FLOOR, MIN_STD_RATIO * float(np.std(y_all)))

def compute_metrics(y_true, y_pred):
    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = float(r2_score(y_true, y_pred))
    std_p = float(np.std(y_pred))
    bias = float(np.mean(y_pred) - np.mean(y_true))
    penalty = max(0.0, std_threshold - std_p)
    obj  = rmse + 0.30 * mae + 0.20 * abs(bias) + LAM * penalty
    return dict(MAE=mae, RMSE=rmse, R2=r2, std_pred=std_p,
                bias=bias, penalty=penalty, objective=obj)

def loocv_predict(pipe, X, y):
    """LOOCV：训练折内完成所有预处理"""
    loo = LeaveOneOut()
    pred = np.zeros(len(y), dtype=float)
    for tr, te in loo.split(X):
        m = clone(pipe)
        m.fit(X[tr], y[tr])
        pred[te[0]] = float(m.predict(X[te])[0])
    return pred

# ── 候选模型定义 ─────────────────────────────────────────
gpr_kernel = (C(1.0, (1e-2, 1e2)) *
              RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e2)) +
              WhiteKernel(noise_level=1e-2, noise_level_bounds=(1e-6, 1e0)))

# PLS 需要 2D y
def loocv_predict_pls(n_components, X, y):
    loo = LeaveOneOut()
    pred = np.zeros(len(y), dtype=float)
    imp = SimpleImputer(strategy='median')
    scl = StandardScaler()
    pls = PLSRegression(n_components=n_components, scale=True)
    for tr, te in loo.split(X):
        Xi_tr = scl.fit_transform(imp.fit_transform(X[tr]))
        Xi_te = scl.transform(imp.transform(X[te]))
        pls_c = clone(pls)
        pls_c.fit(Xi_tr, y[tr])
        pred[te[0]] = float(pls_c.predict(Xi_te.reshape(1, -1)).ravel()[0])
    return pred

from sklearn.model_selection import ParameterGrid

candidates = []

# 1. SVR_RBF（与 Exp3/models.py 相同：含 TransformedTargetRegressor 对 y 做标准化）
svr_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("select",  SelectKBest(score_func=f_regression, k=6)),
    ("scaler",  StandardScaler()),
    ("model",   TransformedTargetRegressor(regressor=SVR(kernel="rbf"),
                                           transformer=StandardScaler())),
])
svr_grid = {
    "select__k":                  [4, 6, 8, 10, 12],
    "model__regressor__C":        [1, 3, 10],
    "model__regressor__gamma":    [0.1, 0.2, 0.4, 0.8, 1.6],
    "model__regressor__epsilon":  [0.01, 0.04, 0.06, 0.08],
}
candidates.append(("SVR_RBF", "grid", svr_pipe, svr_grid))

# 2. PLSRegression（n_components 1/2/3，函数式LOOCV）
for nc in [1, 2, 3]:
    candidates.append((f"PLS(nc={nc})", "pls", nc, None))

# 3. BayesianRidge
for a1 in [1e-6, 1e-4]:
    br_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("model",   BayesianRidge(alpha_1=a1, lambda_1=a1, max_iter=500)),
    ])
    candidates.append((f"BayesianRidge(a={a1:.0e})", "single", br_pipe, None))

# 4. ARDRegression
ard_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
    ("model",   ARDRegression(max_iter=500)),
])
candidates.append(("ARDRegression", "single", ard_pipe, None))

# 5. GPR（小网格：k × alpha）
gpr_grid = {
    "select__k":            [4, 6, 8],
    "model__alpha":         [1e-6, 1e-4, 1e-2],
}
gpr_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("select",  SelectKBest(score_func=f_regression, k=6)),
    ("scaler",  StandardScaler()),
    ("model",   GaussianProcessRegressor(kernel=gpr_kernel, normalize_y=False, random_state=42)),
])
candidates.append(("GPR", "grid", gpr_pipe, gpr_grid))

# 6. Ridge
ridge_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
    ("model",   Ridge()),
])
ridge_grid = {"model__alpha": [0.01, 0.1, 1, 10, 100]}
candidates.append(("Ridge", "grid", ridge_pipe, ridge_grid))

# ── LOOCV 搜索 ───────────────────────────────────────────
all_results = []
best_by_model = {}   # model_name → best record

print(f"std_threshold = {std_threshold:.6f}")
print()

for item in candidates:
    model_name = item[0]
    mode = item[1]
    print(f"─── {model_name} ───")

    if mode == "pls":
        nc = item[2]
        y_pred = loocv_predict_pls(nc, X_all, y_all)
        m = compute_metrics(y_all, y_pred)
        m.update({"model": model_name, "params": {"n_components": nc},
                  "y_pred": y_pred.tolist()})
        all_results.append(m)
        best_by_model[model_name] = m
        print(f"  obj={m['objective']:.4f}  MAE={m['MAE']:.4f}  RMSE={m['RMSE']:.4f}  "
              f"std_pred={m['std_pred']:.4f}  penalty={m['penalty']:.4f}")

    elif mode == "single":
        pipe = item[2]
        y_pred = loocv_predict(pipe, X_all, y_all)
        m = compute_metrics(y_all, y_pred)
        m.update({"model": model_name, "params": {}, "y_pred": y_pred.tolist()})
        all_results.append(m)
        best_by_model[model_name] = m
        print(f"  obj={m['objective']:.4f}  MAE={m['MAE']:.4f}  RMSE={m['RMSE']:.4f}  "
              f"std_pred={m['std_pred']:.4f}  penalty={m['penalty']:.4f}")

    elif mode == "grid":
        pipe = item[2]
        grid = item[3]
        best_obj = float('inf')
        best_m = None
        total = len(list(ParameterGrid(grid)))
        for i, params in enumerate(ParameterGrid(grid)):
            p = clone(pipe)
            p.set_params(**params)
            y_pred = loocv_predict(p, X_all, y_all)
            m = compute_metrics(y_all, y_pred)
            m.update({"model": model_name, "params": params, "y_pred": y_pred.tolist()})
            all_results.append(m)
            if m['objective'] < best_obj:
                best_obj = m['objective']
                best_m = m
        best_by_model[model_name] = best_m
        print(f"  最优 obj={best_m['objective']:.4f}  MAE={best_m['MAE']:.4f}  "
              f"RMSE={best_m['RMSE']:.4f}  std_pred={best_m['std_pred']:.4f}  "
              f"penalty={best_m['penalty']:.4f}  params={best_m['params']}")

print()

# ── 汇总排名 ────────────────────────────────────────────
print("=" * 70)
print("各模型最优 objective 排名")
print("=" * 70)
ranked = sorted(best_by_model.values(), key=lambda x: x['objective'])
print("%-30s  %7s  %7s  %7s  %7s  %7s  %7s" % (
    "模型", "obj", "MAE", "RMSE", "R2", "std_pred", "penalty"))
print("-" * 80)
for r in ranked:
    print("%-30s  %7.4f  %7.4f  %7.4f  %7.4f  %7.4f  %7.4f" % (
        r['model'], r['objective'], r['MAE'], r['RMSE'],
        r['R2'], r['std_pred'], r['penalty']))

print()

# ── 逐田预测明细（最优模型） ─────────────────────────────
best_overall = ranked[0]
y_pred_best  = np.array(best_overall['y_pred'])

# 等级划分（与原始代码相同逻辑）
std_y  = np.std(y_all)
hi_thr = np.mean(y_all) + 0.15 * std_y
lo_thr = np.mean(y_all) - 0.15 * std_y
def grade(v):
    if v >= hi_thr: return "高产"
    if v <= lo_thr: return "低产"
    return "中产"

print(f"最优模型：{best_overall['model']}（obj={best_overall['objective']:.4f}）")
print("%-4s  %-12s  %-12s  %-6s" % ("田块", "真实产量", "预测产量", "等级"))
print("-" * 38)
for fid, yt, yp in sorted(zip(fields, y_all, y_pred_best), key=lambda x: int(x[0][1:])):
    print("%-4s  %-12.6f  %-12.6f  %-6s" % (fid, yt, yp, grade(yp)))

# ── 保存结果 JSON ─────────────────────────────────────────
# 构建逐田详细对比
per_field_details = {}
for model_name, bm in best_by_model.items():
    yp = np.array(bm['y_pred'])
    per_field_details[model_name] = [
        {"field_id": fid, "y_true": float(yt), "y_pred": float(yp_), "grade": grade(yp_)}
        for fid, yt, yp_ in zip(fields, y_all, yp)
    ]

output_data = {
    "std_threshold": std_threshold,
    "feature_count": len(feature_cols),
    "feature_cols": feature_cols,
    "ranked_summary": [
        {k: v for k, v in r.items() if k != 'y_pred'}
        for r in ranked
    ],
    "best_by_model": {
        name: {k: v for k, v in bm.items() if k != 'y_pred'}
        for name, bm in best_by_model.items()
    },
    "per_field_details": per_field_details,
    "best_overall": {k: v for k, v in best_overall.items() if k != 'y_pred'},
}

out_json = os.path.join(OUT_DIR, '模型对比结果.json')
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存：{out_json}")
