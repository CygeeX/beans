#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 summary 计算逻辑
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_server import build_summary_from_csv

# 测试最近一次运行的 CSV
csv_path = "runs/predict_20260325_112409_2f192a/outputs/预测结果_中文.csv"

print("=" * 60)
print("测试 build_summary_from_csv 函数")
print("=" * 60)

summary = build_summary_from_csv(csv_path)

print("\n" + "=" * 60)
print("测试结果:")
print("=" * 60)

if summary:
    print("✅ summary 计算成功!")
    print(f"\n返回的 summary:")
    import json
    print(json.dumps(summary, ensure_ascii=False, indent=2))
else:
    print("❌ summary 计算失败，返回 None")
