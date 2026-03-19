# =============================================================
# 【文件名称】Dockerfile —— Docker 容器化部署配置
# 【文件作用】将后端服务打包为可独立运行的 Docker 镜像。
#             基于 python:3.9-slim 精简镜像，安装依赖后复制代码，
#             以 uvicorn 启动 FastAPI 服务，对外暴露 8000 端口。
# 【系统位置】soy_core_v1_project/Dockerfile
# 【所属模块】Docker 部署
# 【答辩说明】先安装依赖再复制代码，利用 Docker 层缓存加速重复构建。
#             CMD 指令指定容器启动时自动运行的服务命令，
#             监听 0.0.0.0 保证容器外部网络可正常访问。
# =============================================================
FROM python:3.9-slim

# 让容器里默认就是 UTF-8（中文文件名/输出更稳）
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV LANG=C.UTF-8

WORKDIR /app

# 先装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 再拷贝代码与资源（包含 models/model.pkl 和 input/layout.csv）
COPY . /app

EXPOSE 8000

# 注意：必须是 0.0.0.0，外部机器才能访问
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
