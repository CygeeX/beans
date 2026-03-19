# -*- coding: utf-8 -*-
"""
低产预警 vs 非低产 —— 二分类 LOOCV 评估脚本（v2，修正基线）
====================================================
任务定义：
  正类（低产预警）= 1：真实产量 bottom-5（与三分类低产标签完全一致）
  负类（非低产）  = 0：其余田块（中产 + 高产）

类别分布：正类 n=5，负类 n=10（不均衡比例 1:2）

基线说明（重要）：
  - 多数类基线（始终预测"非低产"）：Accuracy = 10/15 = 66.7%
  - 随机基线（各类等概率）：Balanced Accuracy = 50.0%，AUC = 0.500
  - 不应将二分类 Accuracy 与三分类随机基线（33.3%）比较

所有预处理（标准化、特征选择）均在每折训练集内完成，严格防止信息泄漏。
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import date

from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score,
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, roc_curve, precision_recall_curve
)

# ── 中文字体 ─────────────────────────────────────────────────────
def _find_chinese_font():
    candidates = ["SimHei", "Microsoft YaHei", "SimSun", "NSimSun",
                  "FangSong", "KaiTi", "Arial Unicode MS"]
    available = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in available:
            return c
    return None

_cn_font = _find_chinese_font()
plt.rcParams['font.family'] = [_cn_font, 'DejaVu Sans'] if _cn_font else ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ── 路径 ─────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
TRAINING_CSV = os.path.join(_ROOT, 'outputs', '特征修正版训练结果', '训练样本表.csv')
CLS_JSON     = os.path.join(_ROOT, 'outputs', '分类模型对比', '分类模型对比结果.json')
OUT_DIR      = os.path.join(_ROOT, 'outputs', '低产预警评估')
MULTI_DIR    = os.path.join(_ROOT, 'outputs', '产量等级识别评估')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(MULTI_DIR, exist_ok=True)

print("=" * 65)
print("  豆丰智测 · 低产预警二分类 LOOCV 评估（v2，修正基线）")
print("=" * 65)

# ── 1. 数据加载 ──────────────────────────────────────────────────
df = pd.read_csv(TRAINING_CSV, encoding='utf-8-sig')
y_yield  = df['yield'].values.astype(float)
feat_cols = [c for c in df.columns if c not in ('field_id', 'yield')]
X        = df[feat_cols].values
n        = len(df)
field_ids = df['field_id'].tolist()
print(f"\n[数据] n={n}，特征维度={len(feat_cols)}")

# ── 2. 标签构造（与三分类低产定义完全一致）──────────────────────
k = min(5, max(1, n // 3))           # k=5 for n=15
order_desc = np.argsort(-y_yield)
low_idx = set(order_desc[-k:])       # bottom-k = 低产
y_bin   = np.array([1 if i in low_idx else 0 for i in range(n)])

n_pos = int(y_bin.sum())             # 5
n_neg = n - n_pos                    # 10
majority_baseline_acc = n_neg / n    # 10/15 = 0.6667

print(f"[标签] 正类(低产)={n_pos}，负类(非低产)={n_neg}，比例 {n_pos}:{n_neg}")
print(f"[基线] 多数类基线 Accuracy = {majority_baseline_acc:.3f} ({majority_baseline_acc*100:.1f}%，始终预测非低产)")
print(f"[基线] 随机基线 Balanced Accuracy = 0.500，AUC-ROC = 0.500")
print(f"[低产田块] {[field_ids[i] for i in sorted(low_idx)]}")

# ── 3. 候选模型（所有预处理均在 Pipeline 内，LOOCV 每折隔离）──
SELECT_K = min(12, len(feat_cols))
MODELS = {
    "LogisticRegression": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select",  SelectKBest(score_func=f_classif, k=SELECT_K)),
        ("scaler",  StandardScaler()),
        ("clf",     LogisticRegression(C=1.0, max_iter=2000, random_state=42,
                                       class_weight='balanced', solver='lbfgs')),
    ]),
    "LinearSVC": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select",  SelectKBest(score_func=f_classif, k=SELECT_K)),
        ("scaler",  StandardScaler()),
        ("clf",     LinearSVC(C=1.0, max_iter=10000, random_state=42,
                              class_weight='balanced')),
    ]),
    "RandomForest": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("select",  SelectKBest(score_func=f_classif, k=SELECT_K)),
        ("clf",     RandomForestClassifier(n_estimators=200, max_depth=3,
                                           min_samples_leaf=2, random_state=42,
                                           class_weight='balanced', n_jobs=-1)),
    ]),
}

# ── 4. LOOCV 主循环 ──────────────────────────────────────────────
loo = LeaveOneOut()
model_results = {}

for model_name, pipe in MODELS.items():
    preds  = np.zeros(n, dtype=int)
    scores = np.zeros(n, dtype=float)   # 连续分数用于 ROC/PR-AUC

    for tr_idx, te_idx in loo.split(X):
        pipe.fit(X[tr_idx], y_bin[tr_idx])
        preds[te_idx[0]] = int(pipe.predict(X[te_idx])[0])

        clf = pipe.named_steps['clf']
        try:
            # predict_proba 优先（LogisticRegression, RandomForest）
            scores[te_idx[0]] = float(pipe.predict_proba(X[te_idx])[0, 1])
        except AttributeError:
            # decision_function 用于 LinearSVC（其值越大越倾向正类）
            scores[te_idx[0]] = float(pipe.decision_function(X[te_idx])[0])

    # ── 各指标计算 ──────────────────────────────────────────────
    cm = confusion_matrix(y_bin, preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    acc      = float(accuracy_score(y_bin, preds))
    bal_acc  = float(balanced_accuracy_score(y_bin, preds))
    prec     = float(precision_score(y_bin, preds, zero_division=0))
    rec      = float(recall_score(y_bin, preds, zero_division=0))   # TPR
    spec     = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0     # TNR / Specificity
    f1       = float(f1_score(y_bin, preds, zero_division=0))

    try:
        auc_roc = float(roc_auc_score(y_bin, scores))
    except Exception:
        auc_roc = float('nan')

    try:
        pr_auc = float(average_precision_score(y_bin, scores))
    except Exception:
        pr_auc = float('nan')

    model_results[model_name] = {
        "accuracy": acc,
        "majority_class_baseline_acc": majority_baseline_acc,
        "acc_vs_majority": acc - majority_baseline_acc,   # 负数说明低于多数类基线
        "balanced_accuracy": bal_acc,
        "balanced_acc_vs_random": bal_acc - 0.5,
        "precision_low_yield": prec,
        "recall_low_yield": rec,
        "specificity": spec,
        "f1_low_yield": f1,
        "auc_roc": auc_roc,
        "auc_roc_vs_random": auc_roc - 0.5,
        "pr_auc": pr_auc,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": ["非低产(0)", "低产(1)"],
        "note_cm": "行=真实，列=预测；[[TN,FP],[FN,TP]]",
        "scores_raw": scores.tolist(),
        "preds_bin":  preds.tolist(),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }

    print(f"\n{'─'*55}")
    print(f"  {model_name}")
    print(f"{'─'*55}")
    print(f"  Accuracy        = {acc:.3f} ({acc*100:.1f}%)  [多数类基线 {majority_baseline_acc*100:.1f}%，{'低于' if acc < majority_baseline_acc else '高于'}基线]")
    print(f"  Balanced Acc    = {bal_acc:.3f}               [随机基线 0.500，+{bal_acc-0.5:.3f}]")
    print(f"  AUC-ROC         = {auc_roc:.3f}               [随机基线 0.500，+{auc_roc-0.5:.3f}]")
    print(f"  PR-AUC          = {pr_auc:.3f}               [无信息基线 {n_pos/n:.3f}]")
    print(f"  Recall(低产/TPR) = {rec:.3f}  Specificity = {spec:.3f}")
    print(f"  Precision(低产)  = {prec:.3f}  F1(低产)    = {f1:.3f}")
    print(f"  混淆矩阵: TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    print(f"  低产识别: {tp}/{tp+fn} 块 | 非低产正确保留: {tn}/{tn+fp} 块")


# ── 5. 最佳模型选择（以 AUC-ROC 为主，Balanced Acc 为辅）───────
def _rank(r):
    return (
        r['auc_roc'] if not np.isnan(r['auc_roc']) else 0.0,
        r['balanced_accuracy'],
        r['f1_low_yield'],
    )
best_model_name = max(model_results, key=lambda k: _rank(model_results[k]))
best = model_results[best_model_name]
print(f"\n{'='*55}")
print(f"  最佳模型（主排序：AUC-ROC）: {best_model_name}")
print(f"  AUC-ROC={best['auc_roc']:.3f}  Balanced Acc={best['balanced_accuracy']:.3f}  PR-AUC={best['pr_auc']:.3f}")
print(f"{'='*55}")


# ── 6. ROC 曲线图 ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
colors = {'LogisticRegression': '#2196F3', 'LinearSVC': '#4CAF50', 'RandomForest': '#FF9800'}
lss    = {'LogisticRegression': '-', 'LinearSVC': '--', 'RandomForest': '-.'}

for mname, res in model_results.items():
    fpr, tpr, _ = roc_curve(y_bin, res['scores_raw'])
    auc_v = res['auc_roc']
    lbl   = f"{mname} (AUC={auc_v:.3f})"
    ax.plot(fpr, tpr, label=lbl, color=colors.get(mname, '#999'),
            linestyle=lss.get(mname, '-'), linewidth=2)

ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='随机基线 (AUC=0.500)', alpha=0.6)
ax.set_xlabel('False Positive Rate（非低产→预测低产的比例）', fontsize=10)
ax.set_ylabel('True Positive Rate（低产召回率）', fontsize=10)
ax.set_title('低产预警 ROC 曲线\n（LOOCV，n=15；正类=低产 n=5，负类=非低产 n=10）', fontsize=11)
ax.legend(loc='lower right', fontsize=9)
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.05])
ax.grid(alpha=0.3)
fig.tight_layout()
roc_path = os.path.join(OUT_DIR, 'ROC曲线_低产预警.png')
fig.savefig(roc_path, dpi=150)
plt.close(fig)
print(f"\n[图表] ROC曲线: {roc_path}")


# ── 7. PR 曲线图 ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
no_skill_pr = n_pos / n    # 无信息基线（始终预测正类时的 Precision）
for mname, res in model_results.items():
    p, r, _ = precision_recall_curve(y_bin, res['scores_raw'])
    pr_v    = res['pr_auc']
    lbl     = f"{mname} (PR-AUC={pr_v:.3f})"
    ax.plot(r, p, label=lbl, color=colors.get(mname, '#999'),
            linestyle=lss.get(mname, '-'), linewidth=2)

ax.axhline(y=no_skill_pr, color='k', linestyle='--', linewidth=1,
           label=f'无信息基线 Precision={no_skill_pr:.2f}', alpha=0.6)
ax.set_xlabel('Recall（低产召回率）', fontsize=10)
ax.set_ylabel('Precision（低产精确率）', fontsize=10)
ax.set_title('低产预警 Precision-Recall 曲线\n（LOOCV，n=15；类别不均衡 5:10）', fontsize=11)
ax.legend(loc='upper right', fontsize=9)
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.05])
ax.grid(alpha=0.3)
fig.tight_layout()
pr_path = os.path.join(OUT_DIR, 'PR曲线_低产预警.png')
fig.savefig(pr_path, dpi=150)
plt.close(fig)
print(f"[图表] PR曲线: {pr_path}")


# ── 8. 二分类混淆矩阵图（最佳模型）─────────────────────────────
best_cm  = np.array(model_results[best_model_name]['confusion_matrix'])
labels_x = ['预测：非低产\n（中产+高产）', '预测：低产\n（预警触发）']
labels_y = ['真实：非低产\n（中产+高产）', '真实：低产']
fig, ax = plt.subplots(figsize=(5.5, 4.5))
im = ax.imshow(best_cm, cmap='Greens')
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(labels_x, fontsize=9)
ax.set_yticklabels(labels_y, fontsize=9)
ax.set_xlabel('预测结果', fontsize=11)
ax.set_ylabel('真实标签', fontsize=11)
ax.set_title(
    f'低产预警混淆矩阵\n{best_model_name}（LOOCV, n=15）\n'
    f'AUC={best["auc_roc"]:.3f}  Balanced Acc={best["balanced_accuracy"]:.3f}',
    fontsize=10)
thresh = best_cm.max() / 2
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(best_cm[i, j]),
                ha='center', va='center', fontsize=18, fontweight='bold',
                color='white' if best_cm[i, j] > thresh else 'black')
fig.tight_layout()
cm_path = os.path.join(OUT_DIR, '二分类混淆矩阵_低产预警.png')
fig.savefig(cm_path, dpi=150)
plt.close(fig)
print(f"[图表] 二分类混淆矩阵: {cm_path}")


# ── 9. 三分类混淆矩阵图（来自已有结果）──────────────────────────
with open(CLS_JSON, encoding='utf-8') as f:
    cls_data = json.load(f)
lsvc_result = next(r for r in cls_data['results'] if 'LinearSVC' in r['model'])
cm3 = np.array(lsvc_result['confusion_matrix'])
labels3 = ['高产', '中产', '低产']
fig, ax = plt.subplots(figsize=(6, 5))
ax.imshow(cm3, cmap='Blues')
ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels([f'预测{l}' for l in labels3], fontsize=10)
ax.set_yticklabels([f'真实{l}' for l in labels3], fontsize=10)
ax.set_xlabel('预测等级', fontsize=11)
ax.set_ylabel('真实等级', fontsize=11)
ax.set_title('三分类混淆矩阵\nLinearSVC（LOOCV, n=15）\n定位：辅助等级判断（非精度卖点）', fontsize=11)
thresh3 = cm3.max() / 2
for i in range(3):
    for j in range(3):
        ax.text(j, i, str(cm3[i, j]),
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='white' if cm3[i, j] > thresh3 else 'black')
fig.tight_layout()
cm3_path = os.path.join(MULTI_DIR, '三分类混淆矩阵.png')
fig.savefig(cm3_path, dpi=150)
plt.close(fig)
print(f"[图表] 三分类混淆矩阵: {cm3_path}")

# 误判分布
adjacent_errors = int(cm3[0,1] + cm3[1,0] + cm3[1,2] + cm3[2,1])
cross_errors    = int(cm3[0,2] + cm3[2,0])
total_errors    = int(cm3.sum() - np.trace(cm3))


# ── 10. 保存 JSON（修正版）────────────────────────────────────────
summary = {
    "schema_version": "v2_baseline_corrected",
    "task": "低产预警 vs 非低产（二分类 LOOCV）",
    "n_samples": n,
    "n_pos": n_pos,
    "n_neg": n_neg,
    "class_ratio": f"{n_pos}:{n_neg}（低产:非低产）",
    "label_definition": {
        "positive_1": "低产（真实产量 bottom-5，与三分类低产标签一致）",
        "negative_0": "非低产（中产+高产）",
        "low_yield_fields": [field_ids[i] for i in sorted(low_idx)],
    },
    "evaluation": "LOOCV（Leave-One-Out，n=15）",
    "generated_at": str(date.today()),
    "baselines": {
        "majority_class_acc": majority_baseline_acc,
        "majority_class_acc_display": f"{majority_baseline_acc*100:.1f}%（始终预测非低产）",
        "random_balanced_acc": 0.5,
        "random_auc_roc": 0.5,
        "pr_auc_no_skill": round(n_pos / n, 4),
        "note": "二分类中不应与三分类随机基线(33.3%)比较"
    },
    "models": {
        name: {
            "accuracy": res["accuracy"],
            "accuracy_vs_majority_baseline": res["acc_vs_majority"],
            "balanced_accuracy": res["balanced_accuracy"],
            "balanced_acc_vs_random_0_5": res["balanced_acc_vs_random"],
            "precision_low_yield": res["precision_low_yield"],
            "recall_low_yield":    res["recall_low_yield"],
            "specificity":         res["specificity"],
            "f1_low_yield":        res["f1_low_yield"],
            "auc_roc":             res["auc_roc"],
            "auc_roc_vs_random":   res["auc_roc_vs_random"],
            "pr_auc":              res["pr_auc"],
            "confusion_matrix":    res["confusion_matrix"],
            "note_cm":             "行=真实，列=预测；[[TN,FP],[FN,TP]]",
            "tn": res["tn"], "fp": res["fp"],
            "fn": res["fn"], "tp": res["tp"],
        }
        for name, res in model_results.items()
    },
    "best_model": best_model_name,
    "best_model_note": "主排序依据 AUC-ROC（最能反映模型真实区分能力，不受类别不均衡影响）",
    "best_model_metrics": {
        "balanced_accuracy": best["balanced_accuracy"],
        "auc_roc":           best["auc_roc"],
        "pr_auc":            best["pr_auc"],
        "recall_low_yield":  best["recall_low_yield"],
        "specificity":       best["specificity"],
        "f1_low_yield":      best["f1_low_yield"],
        "confusion_matrix":  best["confusion_matrix"],
    },
    "multiclass_reference": {
        "model": "LinearSVC",
        "accuracy": lsvc_result["accuracy"],
        "macro_f1": lsvc_result["macro_f1"],
        "bottom5_low_hit_rate": lsvc_result["bottom5_low_hit_rate"],
        "adjacent_errors": adjacent_errors,
        "cross_grade_errors": cross_errors,
        "total_errors": total_errors,
    },
    "output_files": {
        "roc_curve":             roc_path,
        "pr_curve":              pr_path,
        "binary_confusion_matrix": cm_path,
        "multiclass_confusion_matrix": cm3_path,
    }
}

out_json = os.path.join(OUT_DIR, '低产预警评估结果.json')
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n[JSON] 二分类结果: {out_json}")

mc_json = os.path.join(MULTI_DIR, '三分类误判分析.json')
with open(mc_json, 'w', encoding='utf-8') as f:
    json.dump({
        "task": "三分类（高/中/低产）等级识别 - 辅助等级判断",
        "best_model": "LinearSVC",
        "evaluation": "LOOCV（n=15）",
        "generated_at": str(date.today()),
        "metrics": {
            "accuracy": lsvc_result["accuracy"],
            "macro_f1": lsvc_result["macro_f1"],
            "top5_high_hit_rate": lsvc_result["top5_high_hit_rate"],
            "bottom5_low_hit_rate": lsvc_result["bottom5_low_hit_rate"],
            "random_baseline_accuracy": 1/3,
        },
        "confusion_matrix": lsvc_result["confusion_matrix"],
        "confusion_matrix_labels": ["高产", "中产", "低产"],
        "error_analysis": {
            "total_errors": total_errors,
            "adjacent_grade_errors": adjacent_errors,
            "cross_grade_errors": cross_errors,
        },
        "display_position": "辅助等级判断（不作为精度卖点）",
    }, f, ensure_ascii=False, indent=2)
print(f"[JSON] 三分类分析: {mc_json}")

print("\n" + "=" * 65)
print("  全部完成（v2 基线修正版）")
print("=" * 65)
