# -*- coding: utf-8 -*-
# =============================================================
# 【文件名称】api_server.py —— API 主服务入口
# 【文件作用】定义并启动 FastAPI 后端服务，注册全部对外接口。
#             包含健康检查、模型训练、产量预测、展示指标、结果下载
#             五个接口，是整个后端系统的唯一入口文件。
# 【系统位置】soy_core_v1_project/api_server.py
# 【所属模块】API
# 【答辩说明】Docker 容器启动时由 uvicorn 直接运行本文件。
#             答辩时可重点介绍训练与预测的接口分离设计：
#             /train 供管理员重新建模，/predict 供用户直接推理，
#             /display_metrics 为前端提供预计算的展示指标数据。
# =============================================================
"""
豆丰智测 | 大豆估产 API（训练/预测分离版）

接口：
- GET  /health                      健康检查
- POST /train   (ground + yield)    训练模型并保存 models/model.pkl
- POST /predict (ground)            加载 models/model.pkl 进行预测
- GET  /result/{run_id}/{filename}  下载结果文件

说明：
- /train 需要 yield.xlsx（真实产量），因为要训练/评估模型
- /predict 不需要 yield.xlsx，用户只上传 ground.zip 就能预测
"""
import matplotlib
matplotlib.use("Agg")

import json
import os
import uuid
import sqlite3
import hashlib
import hmac

from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from knowledge_base import get_advice_by_condition
from pydantic import BaseModel

from src.pipeline import run_train, run_predict

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.abspath(__file__))

# 展示指标配置文件：位于项目根 outputs/ 下（soy_core_v1_project 的上级目录）
DISPLAY_METRICS_PATH = os.path.normpath(os.path.join(ROOT, "..", "outputs", "展示指标_新版.json"))

RUNS_DIR = os.path.join(ROOT, "runs")
MODELS_DIR = os.path.join(ROOT, "models")

os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")


app = FastAPI(
    title="豆丰智测 | 大豆估产API V1",
    version="1.1"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查接口：返回服务状态及 model.pkl 是否已就绪
@app.get("/health")
def health():
    return {
        "status": "ok",
        "has_model": os.path.exists(MODEL_PATH),
        "model_path": "models/model.pkl" if os.path.exists(MODEL_PATH) else None
    }


def _new_run(prefix: str) -> tuple[str, str]:
    """生成唯一 run_id，并创建 runs/<run_id>/input + outputs 目录"""
    run_id = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_dir = os.path.join(RUNS_DIR, run_id)
    in_dir = os.path.join(run_dir, "input")
    out_dir = os.path.join(run_dir, "outputs")
    os.makedirs(in_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    return run_id, run_dir


async def _save_upload(upload: UploadFile, dst_path: str) -> None:
    """把 UploadFile 保存到本地"""
    with open(dst_path, "wb") as f:
        f.write(await upload.read())


def _get_layout_path(uploaded_layout_path: Optional[str]) -> str:
    """
    获取 layout.csv 的路径：
    - 若用户上传，则用上传的
    - 否则用项目自带 input/layout.csv
    """
    if uploaded_layout_path and os.path.exists(uploaded_layout_path):
        return uploaded_layout_path

    default_layout = os.path.join(ROOT, "input", "layout.csv")
    if os.path.exists(default_layout):
        return default_layout

    raise HTTPException(status_code=400, detail="未提供 layout.csv，且项目中找不到默认 input/layout.csv")


# 训练接口（管理员用）：接收观测数据和真实产量，触发完整训练流程，返回 run_id 和输出文件列表
@app.post("/train")
async def train(
    ground: UploadFile = File(..., description="地面观测压缩包 ground.zip（内含多次Excel）"),
    yield_xlsx: UploadFile = File(..., description="真实产量表 yield.xlsx（含15块田产量）"),
    layout: Optional[UploadFile] = File(None, description="布局文件 layout.csv（可选）")
):
    if not os.path.exists(MODEL_PATH):
        # 训练模式会生成新的模型，所以这里不检查模型是否存在
        pass

    run_id, run_dir = _new_run("train")
    in_dir = os.path.join(run_dir, "input")
    out_dir = os.path.join(run_dir, "outputs")

    ground_path = os.path.join(in_dir, "ground.zip")
    yield_path = os.path.join(in_dir, "yield.xlsx")
    layout_path = os.path.join(in_dir, "layout.csv") if layout is not None else None

    await _save_upload(ground, ground_path)
    await _save_upload(yield_xlsx, yield_path)
    if layout is not None:
        await _save_upload(layout, layout_path)

    layout_final = _get_layout_path(layout_path)

    # 调用训练函数
    outputs = run_train(
        ground_zip_path=ground_path,
        yield_xlsx_path=yield_path,
        layout_csv_path=layout_final,
        out_dir=out_dir,
        model_path=MODEL_PATH
    )

    # ===== 添加决策建议（和 predict 一样的逻辑）=====
    advice_results = []

    # 训练模式下，预测结果文件在 outputs 中
    pred_csv_path = os.path.join(out_dir, "预测结果_中文.csv")
    if os.path.exists(pred_csv_path):
        import pandas as pd
        pred_df = pd.read_csv(pred_csv_path)
        
        for _, row in pred_df.iterrows():
            field_id = row.get("田块", "")
            yield_pred = row.get("预测产量(kg/100株)", 0)
            
            # 根据产量判断长势
            if yield_pred < 250:
                condition = "低产"
            elif yield_pred > 400:
                condition = "高产"
            else:
                condition = "正常"
            
            # 从知识库获取建议
            advice_data = get_advice_by_condition(condition)
            advice_list = advice_data.get("advice", [])
            
            advice_results.append({
                "field_id": field_id,
                "yield_pred": float(yield_pred),
                "condition": condition,
                "advice": advice_list
            })
    
    # 返回结果
    out_files = {k: os.path.basename(v) for k, v in outputs.items() if isinstance(v, str)}
    
    return {
        "run_id": run_id,
        "outputs": out_files,
        "advice": advice_results  # 返回每个田块的建议
    }


# 预测接口（用户用）：只需上传观测数据，加载已有模型直接完成推理，无需提供真实产量
@app.post("/predict")
async def predict(
    ground: UploadFile = File(..., description="地面观测压缩包 ground.zip（内含多次Excel）"),
    layout: Optional[UploadFile] = File(None, description="布局文件 layout.csv（可选）")
):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail="尚未训练模型：请先调用 /train 生成 models/model.pkl")

    run_id, run_dir = _new_run("predict")
    in_dir = os.path.join(run_dir, "input")
    out_dir = os.path.join(run_dir, "outputs")

    ground_path = os.path.join(in_dir, "ground.zip")
    layout_path = os.path.join(in_dir, "layout.csv") if layout is not None else None

    await _save_upload(ground, ground_path)
    if layout is not None:
        await _save_upload(layout, layout_path)

    layout_final = _get_layout_path(layout_path)

    outputs = run_predict(
        ground_zip_path=ground_path,
        layout_csv_path=layout_final,
        out_dir=out_dir,
        model_path=MODEL_PATH
    )

    advice_results = []

    pred_csv_path = os.path.join(out_dir, "预测结果_中文.csv")
    if os.path.exists(pred_csv_path):
        import pandas as pd
        pred_df = pd.read_csv(pred_csv_path)
        
        for _, row in pred_df.iterrows():
            field_id = row.get("田块", "")
            yield_pred = row.get("预测产量(kg/100株)", 0)
            
            if yield_pred < 250:
                condition = "低产"
            elif yield_pred > 400:
                condition = "高产"
            else:
                condition = "正常"
            
            advice = get_advice_by_condition(condition)
            
            advice_results.append({
                "field_id": field_id,
                "yield_pred": float(yield_pred),
                "condition": condition,
                "advice": advice.get("advice", [])
            })
    
    mgmt_json_path = os.path.join(out_dir, "管理建议_中文.json")
    management_advice = []
    if os.path.exists(mgmt_json_path):
        with open(mgmt_json_path, "r", encoding="utf-8") as f:
            management_advice = json.load(f)

    NEW_EVAL_PATH = "/app/outputs/展示指标_新版.json"
    evaluation = {}
    
    if os.path.exists(NEW_EVAL_PATH):
        # 如果新文件存在，使用新文件
        with open(NEW_EVAL_PATH, "r", encoding="utf-8") as f:
            evaluation = json.load(f)
        print(f"使用新评估文件: {NEW_EVAL_PATH}")
    else:
        # 如果新文件不存在，才用 runs 里的旧文件
        eval_json_path = os.path.join(out_dir, "模型评估_中文.json")
        if os.path.exists(eval_json_path):
            with open(eval_json_path, "r", encoding="utf-8") as f:
                evaluation = json.load(f)
            print(f"使用旧评估文件: {eval_json_path}")

    out_files = {k: os.path.basename(v) for k, v in outputs.items() if isinstance(v, str)}
    
    return {
        "run_id": run_id,
        "outputs": out_files
    }

# 展示指标接口：读取预计算的评估指标配置文件，供前端直接展示核心精度数据
@app.get("/display_metrics")
async def display_metrics():
    """
    返回前端展示指标配置（含两大核心指标 main_metrics）。

    核心指标说明：
    - main_metrics[0] 低产田块命中率 80.0% — 三分类 LinearSVC，
      来源：outputs/分类模型对比/分类模型对比结果.json → bottom5_low_hit_rate
    - main_metrics[1] 低产风险预警 AUC-ROC 0.720 — 二分类 RandomForest，
      来源：outputs/低产预警评估/低产预警评估结果.json → models.RandomForest.auc_roc
    两项指标任务不同、模型不同，不可混同描述。
    """
    if not os.path.exists(EVALUATION_FILE):
        return {"error": "评估文件不存在"}
    
    with open(EVALUATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# 结果文件下载接口：按 run_id 和文件名返回对应的预测结果（图片 / CSV / JSON）
@app.get("/result/{run_id}/{filename}")
def download_result(run_id: str, filename: str):
    file_path = os.path.join(RUNS_DIR, run_id, "outputs", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"未找到文件：{run_id}/{filename}")
    return FileResponse(file_path, filename=filename)

class AdviceRequest(BaseModel):
    condition: str

@app.post("/api/get_advice")
async def api_get_advice(request: AdviceRequest):
    advice = get_advice_by_condition(request.condition)
    return {"advice": advice}

#登录注册
USER_DB_PATH = "/app/user_data/users.db"

# 初始化用户数据库
def init_user_db():
    """创建用户表（如果不存在）"""
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表 - 只有用户名和密码
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"用户数据库初始化完成: {USER_DB_PATH}")

# 初始化
init_user_db()

# 获取数据库连接
def get_user_db():
    return sqlite3.connect(USER_DB_PATH)

# 密码加密
def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + ':' + key.hex()

def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, key_hex = password_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return hmac.compare_digest(key, new_key)
    except:
        return False

# ========== 用户模型 ==========
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# ========== 接口 ==========
@app.post("/api/register")
async def register(user: UserRegister):
    """用户注册"""
    conn = get_user_db()
    cursor = conn.cursor()
    
    # 检查用户是否已存在
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 密码加密
    password_hash = hash_password(user.password)
    
    # 插入新用户
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (user.username, password_hash)
    )
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "注册成功"
    }

@app.post("/api/login")
async def login(user: UserLogin):
    """用户登录 - 成功后返回用户信息"""
    conn = get_user_db()
    cursor = conn.cursor()
    
    # 查询用户
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (user.username,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user_id, username, password_hash = row
    
    # 验证密码
    if not verify_password(user.password, password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 登录成功，返回用户基本信息（无token）
    return {
        "success": True,
        "message": "登录成功",
        "user": {
            "id": user_id,
            "username": username
        }
    }
