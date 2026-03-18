# 豆丰智测 Soy Yield API 文档（FastAPI）

## 基础信息
- 基础地址（本机）：`http://127.0.0.1:8000`
- Swagger：`/docs`
- OpenAPI JSON：`/openapi.json`
- 返回格式：JSON（训练/预测）；文件下载为二进制流（/result）

---

## 1) 健康检查

### GET `/health`
**Response 200**
```json
{"status":"ok"}
```

---

## 2) 训练（管理员用）

### POST `/train`
**Content-Type**：`multipart/form-data`

#### Form 参数
- `ground`（file，必填）：地面观测压缩包 `ground.zip`（内含多次 Excel）
- `yield_xlsx`（file，必填）：真实产量表 `yield.xlsx`（含 15 块田产量）
- `layout`（file，可选）：布局文件 `layout.csv`（不传则使用 `input/layout.csv`）

#### Response 200（示例）
```json
{
  "run_id": "train_20260125_003911_0d8bf9",
  "outputs": {
    "training_table": "training_table.csv",
    "predictions_csv": "预测结果_中文.csv",
    "metrics_json": "模型评估_中文.json",
    "heatmap_png": "热力图_中文绿色_3x5.png",
    "compare_png": "高低产对比图_中文绿色.png",
    "advice_json": "管理建议_中文.json",
    "model_pkl": "model.pkl"
  }
}
```

> 说明：`run_id` 是本次任务号；`outputs` 是可下载文件名列表。  
> 文件实际落盘路径：`runs/<run_id>/outputs/<filename>`

#### curl 示例
```bash
curl -X POST "http://127.0.0.1:8000/train" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "ground=@ground.zip" \
  -F "yield_xlsx=@yield.xlsx" \
  -F "layout=@layout.csv"
```

---

## 3) 预测（用户用，镜像内置模型）

### POST `/predict`
**Content-Type**：`multipart/form-data`

#### Form 参数
- `ground`（file，必填）：地面观测压缩包 `ground.zip`
- `layout`（file，可选）：布局文件 `layout.csv`（不传则使用 `input/layout.csv`）

#### Response 200（示例）
```json
{
  "run_id": "predict_20260125_010203_ab12cd",
  "outputs": {
    "predictions_csv": "预测结果_中文.csv",
    "metrics_json": "模型评估_中文.json",
    "heatmap_png": "热力图_中文绿色_3x5.png",
    "compare_png": "高低产对比图_中文绿色.png",
    "advice_json": "管理建议_中文.json"
  }
}
```

#### 可能错误
- **400**：`尚未训练模型：请先调用 /train 生成 models/model.pkl`  
  > 交付版镜像里已内置 `models/model.pkl`，正常不会出现。

#### curl 示例
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "ground=@ground.zip" \
  -F "layout=@layout.csv"
```

---

## 4) 下载结果文件

### GET `/result/{run_id}/{filename}`

- `run_id`：上一步 `/train` 或 `/predict` 返回的 `run_id`
- `filename`：上一步 `outputs` 里列出的文件名（**必须完全一致**）

#### 示例
- 下载模型：
  - `/result/train_20260125_003911_0d8bf9/model.pkl`
- 下载预测 CSV：
  - `/result/train_20260125_003911_0d8bf9/预测结果_中文.csv`

> 提醒：文件名含中文时，直接复制到浏览器通常也能下载；但命令行工具可能需要 URL 编码。  
> **最推荐**：在 Swagger 的 `/result` 接口里填 `run_id` 和 `filename`，点 **Execute** → **Download**。

---

## 5) 结果文件说明（outputs 各文件含义）

- `training_table.csv`：训练用总表（特征+真实产量合并）
- `预测结果_中文.csv`：训练集预测/或用户预测的结果表
- `模型评估_中文.json`：LOOCV 指标与模型权重等信息
- `热力图_中文绿色_3x5.png`：产量热力图（按 layout 排列）
- `高低产对比图_中文绿色.png`：高/低产对比可视化
- `管理建议_中文.json`：管理建议输出
- `model.pkl`：最终模型（供后续 `/predict` 使用）
