# -*- coding: utf-8 -*-
"""
Exp2：修复 transform_feature_table() 后的训练（路线A生效版）
输出到 outputs/特征修正版训练结果/（当前主输出目录）
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'soy_core_v1_project'))
sys.path.insert(0, PROJECT_ROOT)

INPUT_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'inputs_best_accuracy'))
OUT_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', '特征修正版训练结果'))
MODEL_PATH = os.path.join(OUT_DIR, 'model.pkl')

GROUND_ZIP = os.path.join(INPUT_DIR, 'ground_clean_domaincap.zip')
YIELD_XLSX = os.path.join(INPUT_DIR, 'yield_clean.xlsx')
LAYOUT_CSV = os.path.join(INPUT_DIR, 'layout.csv')

os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 60)
print("豆丰智测 | Exp2：transform_feature_table() 修复后训练")
print("=" * 60)
print(f"ground: {GROUND_ZIP}")
print(f"yield:  {YIELD_XLSX}")
print(f"layout: {LAYOUT_CSV}")
print(f"output: {OUT_DIR}")
print()

from src.pipeline import run_train

outputs = run_train(
    ground_zip_path=GROUND_ZIP,
    yield_xlsx_path=YIELD_XLSX,
    layout_csv_path=LAYOUT_CSV,
    out_dir=OUT_DIR,
    model_path=MODEL_PATH
)

metrics_path = outputs.get('metrics_json', os.path.join(OUT_DIR, '模型评估_中文.json'))
with open(metrics_path, encoding='utf-8') as f:
    metrics = json.load(f)

print()
print("=" * 60)
print("Exp2 训练完成 — 结果汇总")
print("=" * 60)
print(f"最优模型:      {metrics['最优模型']}")
print(f"最优参数:      {json.dumps(metrics['最优参数'], ensure_ascii=False)}")
print(f"MAE:           {metrics['平均绝对误差MAE']:.6f}")
print(f"RMSE:          {metrics['均方根误差RMSE']:.6f}")
print(f"R2:            {metrics['决定系数R2']:.6f}")
print(f"std_pred:      {metrics['预测值标准差std_pred']:.6f}")
print(f"objective:     {metrics['本次最优objective']:.6f}")
print(f"bias:          {metrics['均值偏差bias']:.6f}")
print(f"std_threshold: {metrics['防塌缩阈值std_threshold']:.6f}")
print()

# 读取训练表列名
import csv
train_table_path = outputs.get('training_table', os.path.join(OUT_DIR, '训练样本表.csv'))
with open(train_table_path, encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    cols = next(reader)
print(f"训练样本表.csv 列数: {len(cols)}")
print(f"列名: {cols}")
print()

# 读取预测结果
pred_path = outputs.get('predictions_csv', os.path.join(OUT_DIR, '预测结果_中文.csv'))
with open(pred_path, encoding='utf-8-sig') as f:
    preds = list(csv.DictReader(f))
print("LOOCV 预测结果:")
print("%-4s  %-12s  %-12s  %-6s" % ("田块", "真实产量", "预测产量", "等级"))
print("-" * 40)
for r in preds:
    print("%-4s  %-12s  %-12s  %-6s" % (
        r.get('田块', ''),
        r.get('真实产量(kg/100株)', ''),
        r.get('预测产量(kg/100株)', ''),
        r.get('等级', '')
    ))
print()
print("输出文件：")
for k, v in outputs.items():
    print(f"  {k}: {v}")
