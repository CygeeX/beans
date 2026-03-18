# -*- coding: utf-8 -*-
# =============================================================
# 【文件名称】plotter.py —— 可视化图表生成模块
# 【文件作用】生成两种核心图表：
#             1. 15块田空间热力图（3×5网格，绿色系，标注 Top3/Bottom3）；
#             2. 高低产田块关键特征对比柱状图。
#             图表结果由 API 接口返回前端直接下载展示。
# 【系统位置】soy_core_v1_project/src/plotter.py
# 【所属模块】可视化 / API
# 【答辩说明】热力图直观展示15块田的空间产量分布差异；
#             对比图从特征维度解释高低产田块的生长差异；
#             两张图是答辩可视化展示的核心材料。
# =============================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _setup_cn_font():
    # 中文字体兼容：按顺序尝试
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


# 热力图生成：将15块田产量映射到3×5空间网格，绿色系配色，实线框标注Top3、虚线框标注Bottom3
def plot_heatmap_grid(df_pred_cn: pd.DataFrame, layout_csv_path: str, out_png: str):
    '''
    中文绿色热力图（3×5网格）：
    - 每格显示：T编号 + 预测值
    - Top3/Bottom3 用加粗/虚线边框标注
    '''
    _setup_cn_font()

    layout = pd.read_csv(layout_csv_path)
    merged = layout.merge(df_pred_cn[["田块", "预测产量(kg/100株)"]],
                          left_on="field_id", right_on="田块", how="left")

    nrows = int(merged["row"].max())
    ncols = int(merged["col"].max())

    grid = np.full((nrows, ncols), np.nan, dtype=float)
    label = np.full((nrows, ncols), "", dtype=object)

    for _, r in merged.iterrows():
        i = int(r["row"]) - 1
        j = int(r["col"]) - 1
        v = float(r["预测产量(kg/100株)"])
        grid[i, j] = v
        label[i, j] = f"{r['field_id']}\n{v:.2f}"

    tmp = df_pred_cn.sort_values("预测产量(kg/100株)", ascending=False)
    top3 = set(tmp.head(3)["田块"].tolist())
    bot3 = set(tmp.tail(3)["田块"].tolist())

    fig, ax = plt.subplots(figsize=(10.8, 5.6), dpi=180)

    # 绿色系：YlGn（农业风）
    im = ax.imshow(grid, aspect="auto", interpolation="nearest", cmap="YlGn")

    vmin, vmax = np.nanmin(grid), np.nanmax(grid)
    for i in range(nrows):
        for j in range(ncols):
            v = grid[i, j]
            if np.isnan(v):
                continue
            color = "white" if (v - vmin) / (vmax - vmin + 1e-9) > 0.55 else "black"
            ax.text(j, i, label[i, j], ha="center", va="center",
                    fontsize=12, fontweight="bold", color=color)

    # Top3/Bottom3 边框
    for _, r in layout.iterrows():
        fid = r["field_id"]
        i = int(r["row"]) - 1
        j = int(r["col"]) - 1

        if fid in top3:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                 edgecolor="#0B3D2E", linewidth=4.0, linestyle="-")
            ax.add_patch(rect)
        if fid in bot3:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                 edgecolor="#0B3D2E", linewidth=3.0, linestyle="--")
            ax.add_patch(rect)

    ax.set_xticks(range(ncols))
    ax.set_yticks(range(nrows))
    ax.set_xticklabels([f"列{c+1}" for c in range(ncols)])
    ax.set_yticklabels([f"行{r+1}" for r in range(nrows)])

    ax.set_title("大豆田块预测产量热力图（3×5网格，单位：kg/100株）",
                 fontsize=22, fontweight="bold", pad=18)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    cbar.set_label("预测产量（kg/100株）", fontsize=12)

    fig.text(0.01, 0.02, "加粗边框：Top3    虚线边框：Bottom3",
             fontsize=12, color="#204A3A")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


# 高低产对比图：取产量最高和最低各3块田，对比其 SPAD 均值、株高趋势等关键特征的差异
def plot_top_bottom_compare(df_train: pd.DataFrame, df_pred_cn: pd.DataFrame, out_png: str):
    '''
    高/低产田块关键特征对比（中文+绿色）
    '''
    _setup_cn_font()

    merged = df_train.merge(df_pred_cn[["田块", "预测产量(kg/100株)"]],
                            left_on="field_id", right_on="田块", how="left")

    top = merged.sort_values("预测产量(kg/100株)", ascending=False).head(3)
    bot = merged.sort_values("预测产量(kg/100株)", ascending=True).head(3)

    prefer = ["spad_last", "height_last", "spad_trend", "height_trend"]
    feat_cols = [c for c in prefer if c in merged.columns]
    if len(feat_cols) < 2:
        numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in ["yield", "预测产量(kg/100株)"]]
        feat_cols = numeric_cols[:4]

    top_mean = top[feat_cols].mean()
    bot_mean = bot[feat_cols].mean()

    x = np.arange(len(feat_cols))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10.8, 4.8), dpi=180)
    ax.bar(x - width/2, top_mean.values, width, label="高产组（Top3）", color="#2E8B57")
    ax.bar(x + width/2, bot_mean.values, width, label="低产组（Bottom3）", color="#9FD3A8")

    name_map = {
        "spad_last": "末次SPAD均值",
        "height_last": "末次株高均值",
        "spad_trend": "SPAD变化趋势",
        "height_trend": "株高变化趋势",
    }
    labels = [name_map.get(c, c) for c in feat_cols]

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_title("高/低产田块关键特征对比", fontsize=18, fontweight="bold", pad=10)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
