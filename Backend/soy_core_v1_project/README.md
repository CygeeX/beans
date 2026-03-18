# 豆丰智测 Soy Yield API（Release 交付版）

本仓库提供一个可直接容器化部署的 **FastAPI 后端服务**，用于大豆估产的训练与预测。

- **默认已内置训练好的模型**：`models/model.pkl`  
  ✅ 部署后可直接调用 **`POST /predict`** 进行预测（无需先 `/train`）。
- 同时保留 **`POST /train`**：可在需要时用带真实产量的样本重新训练，并更新 `models/model.pkl`。

---

## 1. 目录结构（交付内容）

建议后端同学拿到的发布目录至少包含：

```
soy_core_v1_project/
├─ api_server.py
├─ requirements.txt
├─ Dockerfile
├─ .dockerignore
├─ src/
│  ├─ io_utils.py
│  ├─ models.py
│  ├─ pipeline.py
│  └─ plotter.py
├─ input/
│  └─ layout.csv            # 默认布局（重要：未上传layout时会用它）
└─ models/
   └─ model.pkl             # ✅ 已训练好的最终模型（重要）
```

> 说明：  
> - `runs/` 是运行时产生的目录（训练/预测的输出都在这里），可以 **不随交付包提交**。  
> - 预测所需的 `ground.zip` 是用户输入数据，不建议打进镜像；可作为 demo 单独提供。

---

## 2. 快速启动（Docker）

### 2.1 构建镜像
在 `soy_core_v1_project/` 目录下执行：

```bash
docker build -t soy-yield-api:release .
```

### 2.2 运行容器
```bash
docker run --rm -p 8000:8000 soy-yield-api:release
```

启动后访问：
- Swagger UI：`http://<host>:8000/docs`
- 健康检查：`http://<host>:8000/health`

### 2.3（推荐）挂载数据卷，持久化 runs/ 与 models/
如果希望 **训练后模型与输出可持久化**（容器重启不丢失）：

```bash
docker run --rm -p 8000:8000   -v /path/on/host/runs:/app/runs   -v /path/on/host/models:/app/models   soy-yield-api:release
```

> 容器内默认路径以 `api_server.py` 所在目录为根（ROOT）。  
> 代码里 `runs/` 与 `models/` 都在同级目录下。

---

## 3. 输入数据说明

### 3.1 `ground.zip`（必需：训练与预测都要）
- **类型**：zip 压缩包
- **内容**：多次地面观测的 Excel 文件（项目已有解析逻辑，按现有格式输入即可）

### 3.2 `yield.xlsx`（仅训练需要）
- **类型**：Excel
- **内容**：真实产量表（例如 15 块田的真实产量）
- **用途**：用于训练与交叉验证评估

### 3.3 `layout.csv`（可选，但必须存在默认）
- **类型**：CSV
- **用途**：用于绘制热力图的布局  
- **规则**：
  - 若请求上传了 `layout.csv` → 使用上传的
  - 否则使用项目内置 `input/layout.csv`
  - 若两者都没有 → 接口返回 400

---

## 4. 接口概览

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health` | 健康检查（是否内置模型） |
| POST | `/predict` | 使用 `models/model.pkl` 预测（无需产量表） |
| POST | `/train` | 使用 `ground.zip + yield.xlsx` 训练并更新模型 |
| GET | `/result/{run_id}/{filename}` | 下载某次运行生成的输出文件 |

详细字段与示例见：[`API.md`](./API.md)

---

## 5. 交付给后端同学的建议

### 5.1 你需要交付什么？
- ✅ **整个 `soy_core_v1_project/` 文件夹**（含 Dockerfile、requirements、src、input/layout.csv、models/model.pkl）

### 5.2 你不需要交付什么？
- ❌ 你本机 Swagger 下载出来的那些 `runs/<run_id>/outputs/*` 文件（除非你想当作 demo 样例）
- ❌ 本机 Anaconda 环境（后端会用 Docker 构建）

---

## 6. 版本信息
- API：FastAPI + Uvicorn
- Python 依赖：见 `requirements.txt`
- 模型文件：`models/model.pkl`

