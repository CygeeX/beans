# -*- coding: utf-8 -*-
# =============================================================
# 【文件名称】pipeline.py —— 训练与预测流水线
# 【文件作用】将数据读取、特征工程、模型训练/评估、图表生成、
#             结果文件导出串联为完整的端到端流程。
#             是 API 层与底层算法模块之间的调度中枢。
# 【系统位置】soy_core_v1_project/src/pipeline.py
# 【所属模块】API / 模型推理
# 【答辩说明】run_train() 展示从原始数据到评估结果的完整训练步骤；
#             run_predict() 展示用户仅上传观测数据即可获得预测结果
#             的轻量化推理流程，体现训练与预测的逻辑分离。
# =============================================================
import os
import json
import shutil

from .io_utils import build_training_table, build_feature_table, make_advice_rules
from .models import (
    transform_feature_table,
    loocv_train_predict,
    fit_full_model, save_model, load_model, predict_with_model, make_pred_dataframe
)
from .plotter import plot_heatmap_grid, plot_top_bottom_compare


# 完整训练流程：特征工程 → LOOCV 评估 → 全量训练 → 图表生成 → 结果文件导出
def run_train(ground_zip_path: str,
              yield_xlsx_path: str,
              layout_csv_path: str,
              out_dir: str,
              model_path: str) -> dict:
    """
    训练模式（管理员用）：
    1) 特征工程 + 合并真实产量 -> training_table.csv
    2) LOOCV评估 + 训练集预测 -> 预测结果_中文.csv + 模型评估_中文.json
    3) 生成热力图/对比图 + 建议
    4) 用全量数据训练“最终模型”并保存到 model_path（供 /predict 使用）
    同时：复制一份 model.pkl 到 out_dir 根目录，供 /result/{run_id}/model.pkl 下载
    """
    os.makedirs(out_dir, exist_ok=True)

    # 1) 构建训练表（原始特征）
    df_train = build_training_table(ground_zip_path, yield_xlsx_path)

    # ✅ 路线A：强压缩/去噪/变化量特征（训练/预测必须一致）
    df_train = transform_feature_table(df_train)

    train_path = os.path.join(out_dir, "training_table.csv")
    df_train.to_csv(train_path, index=False, encoding="utf-8-sig")

    # 2) LOOCV 评估 + 训练集预测
    df_pred_cn, metrics_cn = loocv_train_predict(df_train)

    pred_path = os.path.join(out_dir, "预测结果_中文.csv")
    metrics_path = os.path.join(out_dir, "模型评估_中文.json")
    df_pred_cn.to_csv(pred_path, index=False, encoding="utf-8-sig")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_cn, f, ensure_ascii=False, indent=2)

    # 3) 保存最终模型（给 /predict 用：保存到 model_path）
    best_name = metrics_cn.get("最优模型")
    best_params = metrics_cn.get("最优参数")
    bundle = fit_full_model(df_train, best_model_name=best_name, best_params=best_params)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    save_model(bundle, model_path)

    # ✅ 关键：再复制一份到本次 run 的 outputs 根目录，保证 /result 能下载到
    model_out_path = os.path.join(out_dir, "model.pkl")
    try:
        shutil.copy2(model_path, model_out_path)
    except Exception:
        # 如果复制失败但 model_path 就在 out_dir 里，也不影响（尽量兜底）
        if os.path.abspath(os.path.dirname(model_path)) != os.path.abspath(out_dir):
            raise

    # 4) 生成图表
    heatmap_path = os.path.join(out_dir, "热力图_中文绿色_3x5.png")
    compare_path = os.path.join(out_dir, "高低产对比图_中文绿色.png")
    plot_heatmap_grid(df_pred_cn, layout_csv_path, heatmap_path)
    plot_top_bottom_compare(df_train, df_pred_cn, compare_path)

    # 5) 管理建议
    advice = make_advice_rules(df_train, df_pred_cn)
    advice_path = os.path.join(out_dir, "管理建议_中文.json")
    with open(advice_path, "w", encoding="utf-8") as f:
        json.dump(advice, f, ensure_ascii=False, indent=2)

    # ✅ 注意：这里返回 model_out_path（run 的 outputs 下的 model.pkl）
    # 这样前端/Swagger 显示与 /result 下载逻辑完全一致
    return {
        "training_table": train_path,
        "predictions_csv": pred_path,
        "metrics_json": metrics_path,
        "heatmap_png": heatmap_path,
        "compare_png": compare_path,
        "advice_json": advice_path,
        "model_pkl": model_out_path
    }


# 完整预测流程：特征构建 → 特征压缩 → 加载已有模型 → 推理 → 图表生成（无需真实产量）
def run_predict(ground_zip_path: str,
                layout_csv_path: str,
                out_dir: str,
                model_path: str) -> dict:
    """
    预测模式（用户用）：
    - 不需要真实产量 yield.xlsx
    - 读取 ground.zip -> 生成特征表 -> 加载 model.pkl -> 预测产量
    - 输出：预测结果 + 热力图 + 对比图 + 建议
    """
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"找不到模型文件：{model_path}，请先调用 /train 训练生成 model.pkl")

    # 1) 构建特征表（原始特征）
    df_feat = build_feature_table(ground_zip_path)

    # ✅ 必须与训练保持一致的强压缩特征变换
    df_feat = transform_feature_table(df_feat)

    # 2) 加载模型并预测
    bundle = load_model(model_path)
    y_pred = predict_with_model(bundle, df_feat)
    df_pred_cn = make_pred_dataframe(df_feat, y_pred)

    pred_path = os.path.join(out_dir, "预测结果_中文.csv")
    df_pred_cn.to_csv(pred_path, index=False, encoding="utf-8-sig")

    # ===== 修改1：模型评估文件 - 优先使用新文件 =====
    metrics_path = os.path.join(out_dir, "展示指标_新版.json")
    
    # 尝试读取新的展示指标文件
    NEW_EVAL_PATH = "/app/outputs/展示指标_新版.json"
    if os.path.exists(NEW_EVAL_PATH):
        # 如果新文件存在，直接复制过来
        import shutil
        shutil.copy2(NEW_EVAL_PATH, metrics_path)
        print(f"已使用新评估文件: {NEW_EVAL_PATH}")
    else:
        # 如果新文件不存在，才生成说明文件
        metrics_cn = {
            "说明": "当前为预测模式（无真实产量），不计算MAE/RMSE/R2。若需评估请使用 /train 并提供 yield.xlsx。",
            "模型信息": {"模型文件": os.path.basename(model_path)}
        }
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_cn, f, ensure_ascii=False, indent=2)

    heatmap_path = os.path.join(out_dir, "热力图_中文绿色_3x5.png")
    compare_path = os.path.join(out_dir, "高低产对比图_中文绿色.png")
    plot_heatmap_grid(df_pred_cn, layout_csv_path, heatmap_path)
    plot_top_bottom_compare(df_feat, df_pred_cn, compare_path)

    # ===== 修改2：决策建议 - 从知识库获取，替代原来的 make_advice_rules =====
    advice_path = os.path.join(out_dir, "管理建议_中文.json")
    
    # 导入知识库函数
    import sys
    import os as os_module
    sys.path.append(os_module.path.dirname(os_module.path.dirname(__file__)))
    try:
        from knowledge_base import get_advice_by_condition
    except ImportError:
        # 如果导入失败，回退到原有建议
        print("警告: 无法导入 knowledge_base，使用原有建议规则")
        advice = make_advice_rules(df_feat, df_pred_cn)
        with open(advice_path, "w", encoding="utf-8") as f:
            json.dump(advice, f, ensure_ascii=False, indent=2)
    else:
        # 根据预测结果生成决策建议
        advice_results = []
        
        for _, row in df_pred_cn.iterrows():
            field_id = row.get("田块", "")
            yield_pred = row.get("预测产量(kg/100株)", 0)
            
            # 根据产量判断长势（阈值可根据需要调整）
            if yield_pred < 250:
                condition = "低产"
            elif yield_pred > 400:
                condition = "高产"
            else:
                condition = "正常"
            
            # 从知识库获取建议
            advice = get_advice_by_condition(condition)
            
            advice_results.append({
                "field_id": field_id,
                "yield_pred": float(yield_pred),
                "condition": condition,
                "advice": advice.get("advice", [])
            })
        
        # 保存建议到文件
        with open(advice_path, "w", encoding="utf-8") as f:
            json.dump(advice_results, f, ensure_ascii=False, indent=2)

    return {
        "predictions_csv": pred_path,
        "metrics_json": metrics_path,
        "heatmap_png": heatmap_path,
        "compare_png": compare_path,
        "advice_json": advice_path,
    }


def run_all(ground_zip_path: str, yield_xlsx_path: str, layout_csv_path: str, out_dir: str) -> dict:
    """
    兼容旧接口：仍然支持一键跑通（会训练并输出结果）
    """
    model_dir = os.path.join(out_dir, "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.pkl")
    return run_train(ground_zip_path, yield_xlsx_path, layout_csv_path, out_dir, model_path=model_path)