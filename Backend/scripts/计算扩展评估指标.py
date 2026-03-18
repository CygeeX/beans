# -*- coding: utf-8 -*-
"""
Exp3 扩展评估指标计算：保留原有回归指标 + 新增排序/稳健误差/平台应用指标
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'soy_core_v1_project'))
sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import csv
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, balanced_accuracy_score, f1_score,
    median_absolute_error, confusion_matrix
)

# ── 读取 Exp3 预测结果 ─────────────────────────────────────
PRED_CSV   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果', '预测结果_中文.csv'))
METRICS_J  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果', '模型评估_中文.json'))
OUT_JSON   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果', '扩展评估指标.json'))

with open(PRED_CSV, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

rows_sorted = sorted(rows, key=lambda x: int(x['田块'][1:]))
fields  = [r['田块'] for r in rows_sorted]
y_true  = np.array([float(r['真实产量(kg/100株)']) for r in rows_sorted])
y_pred  = np.array([float(r['预测产量(kg/100株)']) for r in rows_sorted])
pred_grade_csv = [r['等级'] for r in rows_sorted]

with open(METRICS_J, encoding='utf-8') as f:
    orig_metrics = json.load(f)

n = len(y_true)

# ── 等级划分函数（与 loocv_train_predict 完全一致） ──────────
def assign_grades(y):
    k = min(5, max(1, n // 3))  # = 5 for n=15
    order = np.argsort(-y)
    grade = np.array(['中产'] * n, dtype=object)
    grade[order[:k]] = '高产'
    grade[order[-k:]] = '低产'
    return grade

pred_grade = assign_grades(y_pred)
true_grade = assign_grades(y_true)

# 验证与 CSV 一致
assert list(pred_grade) == pred_grade_csv, f"等级不一致: {list(pred_grade)} vs {pred_grade_csv}"
print("✅ 等级划分验证通过（与 CSV 完全一致）")
print()

# ── 原有回归指标 ──────────────────────────────────────────
mae     = float(mean_absolute_error(y_true, y_pred))
rmse    = float(np.sqrt(mean_squared_error(y_true, y_pred)))
r2      = float(r2_score(y_true, y_pred))
bias    = float(np.mean(y_pred) - np.mean(y_true))
std_pred_ = float(np.std(y_pred))
std_true_ = float(np.std(y_true))
obj     = orig_metrics['本次最优objective']
std_thr = orig_metrics['防塌缩阈值std_threshold']

# ── 新增：排序类指标 ──────────────────────────────────────
rho, rho_p  = spearmanr(y_true, y_pred)
tau, tau_p  = kendalltau(y_true, y_pred)

# ── 新增：稳健误差指标 ────────────────────────────────────
med_ae  = float(median_absolute_error(y_true, y_pred))
nrmse_mean  = rmse / float(np.mean(y_true))
nrmse_range = rmse / float(np.ptp(y_true))   # ptp = max - min

# ── 新增：平台应用指标 ────────────────────────────────────
label_map  = {'高产': 2, '中产': 1, '低产': 0}
true_int   = np.array([label_map[g] for g in true_grade])
pred_int   = np.array([label_map[g] for g in pred_grade])

acc        = float(accuracy_score(true_int, pred_int))
bal_acc    = float(balanced_accuracy_score(true_int, pred_int))
macro_f1   = float(f1_score(true_int, pred_int, average='macro', zero_division=0))
cm         = confusion_matrix(true_int, pred_int, labels=[2, 1, 0])

# top-5 命中率：真实产量最高的5块 vs 预测等级=高产的5块
k = 5
true_top5   = set(np.argsort(-y_true)[:k])
pred_top5   = set(np.argsort(-y_pred)[:k])
true_bot5   = set(np.argsort(y_true)[:k])
pred_bot5   = set(np.argsort(y_pred)[:k])

top5_hit  = len(true_top5 & pred_top5) / k
bot5_hit  = len(true_bot5 & pred_bot5) / k

# ── 每类 precision / recall / F1 ────────────────────────
from sklearn.metrics import classification_report
cr = classification_report(true_int, pred_int, labels=[2,1,0],
                           target_names=['高产','中产','低产'],
                           output_dict=True, zero_division=0)

# ── 打印汇总 ──────────────────────────────────────────────
DIVIDER = "=" * 60

print(DIVIDER)
print("一、核心回归指标（原有，保留不变）")
print(DIVIDER)
print(f"  MAE              : {mae:.6f}")
print(f"  RMSE             : {rmse:.6f}")
print(f"  R²               : {r2:.6f}")
print(f"  bias             : {bias:.6f}")
print(f"  objective        : {obj:.6f}")
print(f"  std_pred         : {std_pred_:.6f}")
print(f"  std_true         : {std_true_:.6f}")
print(f"  std_pred/std_true: {std_pred_/std_true_:.6f}")
print()

print(DIVIDER)
print("二、辅助排序指标")
print(DIVIDER)
print(f"  Spearman rho     : {rho:.4f}  (p={rho_p:.4f})")
print(f"  Kendall tau      : {tau:.4f}  (p={tau_p:.4f})")
print()

print(DIVIDER)
print("三、稳健误差指标")
print(DIVIDER)
print(f"  Median AE        : {med_ae:.6f}")
print(f"  NRMSE(mean)      : {nrmse_mean:.4f}  ({nrmse_mean*100:.2f}%)")
print(f"  NRMSE(range)     : {nrmse_range:.4f}  ({nrmse_range*100:.2f}%)")
print()

print(DIVIDER)
print("四、平台应用指标（三分类：高/中/低产）")
print(DIVIDER)
print(f"  Accuracy         : {acc:.4f}  ({acc*100:.1f}%)")
print(f"  Balanced Acc     : {bal_acc:.4f}  ({bal_acc*100:.1f}%)")
print(f"  Macro F1         : {macro_f1:.4f}")
print(f"  Top-5 高产命中率  : {top5_hit:.4f}  ({top5_hit*100:.0f}%)")
print(f"  Bottom-5 低产命中率: {bot5_hit:.4f}  ({bot5_hit*100:.0f}%)")
print()

print("混淆矩阵（行=真实，列=预测）：")
print("              预测高产  预测中产  预测低产")
for i, name in enumerate(['真实高产', '真实中产', '真实低产']):
    print(f"  {name}  {cm[i,0]:4d}      {cm[i,1]:4d}      {cm[i,2]:4d}")
print()

print("各类 F1 / precision / recall：")
for cls in ['高产', '中产', '低产']:
    d = cr[cls]
    print(f"  {cls}：precision={d['precision']:.3f}  recall={d['recall']:.3f}  f1={d['f1-score']:.3f}  support={int(d['support'])}")
print()

print(DIVIDER)
print("五、逐田明细")
print(DIVIDER)
print(f"{'田块':4s}  {'真实产量':10s}  {'预测产量':10s}  {'真实等级':6s}  {'预测等级':6s}  {'等级正确':6s}  {'|误差|':8s}")
print("-" * 60)
for fid, yt, yp, tg, pg in sorted(
        zip(fields, y_true, y_pred, true_grade, pred_grade),
        key=lambda x: int(x[0][1:])):
    ok = '✓' if tg == pg else '✗'
    print(f"{fid:4s}  {yt:10.4f}  {yp:10.4f}  {tg:6s}  {pg:6s}  {ok:6s}  {abs(yt-yp):8.4f}")
print()

# ── 保存 JSON ────────────────────────────────────────────
result = {
    "experiment": "Exp3（去冗余 35 维，SVR_RBF k=12）",
    "n_samples": n,
    "regression_metrics": {
        "MAE": mae, "RMSE": rmse, "R2": r2,
        "bias": bias, "objective": obj,
        "std_pred": std_pred_, "std_true": std_true_,
        "std_pred_over_std_true": std_pred_ / std_true_,
        "std_threshold": std_thr,
    },
    "ranking_metrics": {
        "spearman_rho": float(rho), "spearman_p": float(rho_p),
        "kendall_tau": float(tau), "kendall_p": float(tau_p),
    },
    "robust_error_metrics": {
        "median_AE": med_ae,
        "NRMSE_mean": nrmse_mean,
        "NRMSE_range": nrmse_range,
    },
    "platform_metrics": {
        "accuracy": acc, "balanced_accuracy": bal_acc,
        "macro_F1": macro_f1,
        "top5_high_hit_rate": top5_hit,
        "bottom5_low_hit_rate": bot5_hit,
        "per_class": {cls: cr[cls] for cls in ['高产', '中产', '低产']},
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": ["高产", "中产", "低产"],
    },
    "per_field": [
        {"field_id": fid, "y_true": float(yt), "y_pred": float(yp),
         "true_grade": tg, "pred_grade": pg,
         "correct": (tg == pg), "abs_error": float(abs(yt - yp))}
        for fid, yt, yp, tg, pg in zip(fields, y_true, y_pred, true_grade, pred_grade)
    ],
    "grade_definition": "排名法：预测产量 top-5 = 高产，bottom-5 = 低产，middle-5 = 中产（k=n//3=5）",
    "true_grade_definition": "同一逻辑应用于真实产量，用于分类指标的基准",
}
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"结果已保存：{OUT_JSON}")
