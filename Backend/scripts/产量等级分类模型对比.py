# -*- coding: utf-8 -*-
"""
等级识别分类模型基线实验
对比：LinearSVC / RBF-SVC / RidgeClassifier  vs  Exp3 回归转等级（基线）
评估方式：LOOCV（n=15）
标签定义：真实产量排名 top-5=高产, middle-5=中产, bottom-5=低产
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif
from sklearn.svm import SVC, LinearSVC
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix
)

# ── 路径设置 ─────────────────────────────────────────────────
TRAINING_CSV = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果', '训练样本表.csv'
))
EXP3_JSON = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果', '扩展评估指标.json'
))
OUT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'outputs', '分类模型对比'
))
os.makedirs(OUT_DIR, exist_ok=True)
OUT_JSON = os.path.join(OUT_DIR, '分类模型对比结果.json')

# ── 加载特征表 ────────────────────────────────────────────────
df = pd.read_csv(TRAINING_CSV, encoding='utf-8-sig')
y_true = df['yield'].values.astype(float)
feat_cols = [c for c in df.columns if c not in ('field_id', 'yield')]
X = df[feat_cols].values
n = len(df)
print(f"样本数 n={n}，特征数={len(feat_cols)}")

# ── 真实等级标签（基于真实产量排名，固定不变）─────────────────
k = min(5, max(1, n // 3))   # = 5 for n=15
order_true = np.argsort(-y_true)   # descending
true_label = np.array(['中产'] * n, dtype=object)
true_label[order_true[:k]] = '高产'
true_label[order_true[-k:]] = '低产'
label_map = {'高产': 2, '中产': 1, '低产': 0}
y_cls = np.array([label_map[g] for g in true_label])

# 真实 top-5 / bottom-5 索引
true_top5_idx = set(order_true[:k])
true_bot5_idx = set(order_true[-k:])
print(f"真实高产: {[df['field_id'].iloc[i] for i in order_true[:k]]}")
print(f"真实低产: {[df['field_id'].iloc[i] for i in order_true[-k:]]}")
print()

DIVIDER = "=" * 60

# ── 评估函数 ──────────────────────────────────────────────────
def evaluate(y_pred_cls, name):
    acc = float(accuracy_score(y_cls, y_pred_cls))
    bal = float(balanced_accuracy_score(y_cls, y_pred_cls))
    mf1 = float(f1_score(y_cls, y_pred_cls, average='macro', zero_division=0))
    cm = confusion_matrix(y_cls, y_pred_cls, labels=[2, 1, 0])

    pred_order = np.argsort(-y_pred_cls)   # higher label = 高产
    # top5_hit: intersection of true top-5 idx and predicted "高产" (label=2) idx
    pred_high_idx = set(np.where(y_pred_cls == 2)[0])
    pred_low_idx  = set(np.where(y_pred_cls == 0)[0])
    top5_hit  = len(true_top5_idx & pred_high_idx) / k
    bot5_hit  = len(true_bot5_idx & pred_low_idx)  / k

    print(f"\n{DIVIDER}")
    print(f"  模型：{name}")
    print(DIVIDER)
    print(f"  Accuracy         : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Balanced Acc     : {bal:.4f}  ({bal*100:.1f}%)")
    print(f"  Macro F1         : {mf1:.4f}")
    print(f"  Top-5 高产命中率  : {top5_hit:.4f}  ({top5_hit*100:.0f}%)")
    print(f"  Bottom-5 低产命中率: {bot5_hit:.4f}  ({bot5_hit*100:.0f}%)")
    print("  混淆矩阵（行=真实，列=预测，标签顺序 高/中/低）：")
    print("              预测高产  预测中产  预测低产")
    for i, nm in enumerate(['真实高产', '真实中产', '真实低产']):
        print(f"  {nm}  {cm[i,0]:5d}     {cm[i,1]:5d}     {cm[i,2]:5d}")

    return {
        "model": name,
        "accuracy": acc,
        "balanced_accuracy": bal,
        "macro_f1": mf1,
        "top5_high_hit_rate": top5_hit,
        "bottom5_low_hit_rate": bot5_hit,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": ["高产", "中产", "低产"],
        "n_correct": int(np.sum(y_pred_cls == y_cls)),
        "n_total": n,
    }

# ── LOOCV 通用函数 ────────────────────────────────────────────
def loocv_classify(pipeline, X, y_cls):
    loo = LeaveOneOut()
    preds = np.zeros(len(y_cls), dtype=int)
    for tr, te in loo.split(X):
        pipeline.fit(X[tr], y_cls[tr])
        preds[te[0]] = int(pipeline.predict(X[te])[0])
    return preds

# ── Exp3 回归转等级基线（直接从 JSON 读取已有 LOOCV 结果）──────
print("\n从 扩展评估指标.json 读取基线结果...")
with open(EXP3_JSON, encoding='utf-8') as f:
    exp3 = json.load(f)

# Exp3 的预测等级（基于预测产量排名）
grade_name_map = {'高产': 2, '中产': 1, '低产': 0}
exp3_pred_cls = np.array([
    grade_name_map[r['pred_grade']]
    for r in sorted(exp3['per_field'], key=lambda x: int(x['field_id'][1:]))
])
# 真实等级同样按 T1..T15 排序
exp3_true_cls = np.array([
    grade_name_map[r['true_grade']]
    for r in sorted(exp3['per_field'], key=lambda x: int(x['field_id'][1:]))
])
# 验证：应与我们计算的 y_cls 一致（按 field_id 排序）
df_sorted_idx = [i for i, fid in sorted(enumerate(df['field_id']), key=lambda x: int(x[1][1:]))]
y_cls_sorted = y_cls[df_sorted_idx]
assert list(exp3_true_cls) == list(y_cls_sorted), "真实等级不一致，请检查数据！"
print("✅ 真实等级验证通过")

# 恢复原始索引顺序（与 X 对应）
field_ids = df['field_id'].tolist()
exp3_pred_cls_ordered = np.zeros(n, dtype=int)
for r in exp3['per_field']:
    idx = field_ids.index(r['field_id'])
    exp3_pred_cls_ordered[idx] = grade_name_map[r['pred_grade']]

results = []
res_exp3 = evaluate(exp3_pred_cls_ordered, "Exp3_SVR_RBF_回归转等级（基线）")
results.append(res_exp3)

# ── LinearSVC ─────────────────────────────────────────────────
print("\n\n运行 LinearSVC LOOCV...")
pipe_lsvc = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("select", SelectKBest(score_func=f_classif, k=12)),
    ("scaler", StandardScaler()),
    ("model", LinearSVC(C=1.0, max_iter=10000, random_state=42))
])
pred_lsvc = loocv_classify(pipe_lsvc, X, y_cls)
res_lsvc = evaluate(pred_lsvc, "LinearSVC（C=1, k=12）")
results.append(res_lsvc)

# ── RBF-SVC ──────────────────────────────────────────────────
print("\n\n运行 RBF-SVC LOOCV...")
pipe_rbfsvc = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("select", SelectKBest(score_func=f_classif, k=12)),
    ("scaler", StandardScaler()),
    ("model", SVC(kernel="rbf", C=1.0, gamma=0.2, random_state=42))
])
pred_rbfsvc = loocv_classify(pipe_rbfsvc, X, y_cls)
res_rbfsvc = evaluate(pred_rbfsvc, "RBF-SVC（C=1, γ=0.2, k=12）")
results.append(res_rbfsvc)

# ── RidgeClassifier ──────────────────────────────────────────
print("\n\n运行 RidgeClassifier LOOCV...")
pipe_ridge = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("select", SelectKBest(score_func=f_classif, k=12)),
    ("scaler", StandardScaler()),
    ("model", RidgeClassifier(alpha=1.0))
])
pred_ridge = loocv_classify(pipe_ridge, X, y_cls)
res_ridge = evaluate(pred_ridge, "RidgeClassifier（α=1, k=12）")
results.append(res_ridge)

# ── 随机基线（参考）─────────────────────────────────────────
# 理论随机基线（等概率）: 每次预测各等级概率均等 → accuracy≈33.3%
random_baseline = {
    "model": "随机猜测（等概率，参考基线）",
    "accuracy": 1/3,
    "balanced_accuracy": 1/3,
    "macro_f1": 1/3,
    "top5_high_hit_rate": 1/3,
    "bottom5_low_hit_rate": 1/3,
    "note": "理论值，每次预测对三类等概率猜测时的期望准确率"
}
results.append(random_baseline)

# ── 汇总打印 ──────────────────────────────────────────────────
print(f"\n\n{DIVIDER}")
print("汇总对比（LOOCV n=15，三分类：高/中/低产）")
print(DIVIDER)
print(f"{'模型':35s}  {'Acc':7s}  {'BalAcc':7s}  {'MacF1':7s}  {'Top5H':7s}  {'Bot5L':7s}")
print("-" * 80)
for r in results:
    acc = r['accuracy']
    bal = r['balanced_accuracy']
    f1  = r['macro_f1']
    t5  = r['top5_high_hit_rate']
    b5  = r['bottom5_low_hit_rate']
    name_short = r['model'][:35]
    print(f"{name_short:35s}  {acc:.3f}    {bal:.3f}    {f1:.3f}    {t5:.3f}    {b5:.3f}")

# ── 保存 JSON ────────────────────────────────────────────────
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump({
        "experiment": "等级识别分类模型基线对比",
        "n_samples": n,
        "n_features": len(feat_cols),
        "grade_rule": "真实产量排名：top-5=高产（2），middle-5=中产（1），bottom-5=低产（0），k=5",
        "evaluation": "LOOCV（Leave-One-Out，n=15）",
        "random_baseline_accuracy": 1/3,
        "generated_at": "2026-03-14",
        "results": results
    }, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存：{OUT_JSON}")
