# 豆丰智测 - 快速启动指南

## 前提条件

- Node.js 16+ 已安装
- npm 或 yarn 已安装
- 后端 API 服务已启动（默认端口 8000）

## 快速启动（3 步）

### 1. 安装依赖

```bash
cd my-project
npm install
```

### 2. 配置后端地址

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

如果后端在其他地址，请修改为实际地址。

### 3. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

## 验证安装

### 检查页面是否正常加载

1. 打开浏览器访问 http://localhost:5173
2. 应该看到"豆丰智测"首页
3. 页面显示"即刻估产"标题

### 检查后端连接

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 如果看到网络错误，检查后端服务是否启动

## 测试功能

### 测试文件上传

1. 准备测试文件：
   - `ground.zip`（地面观测数据）
   - `yield.xlsx`（产量记录表，可选）
   - `layout.csv`（布局文件，可选）

2. 在上传页面：
   - 选择"快速预测"或"训练模型"
   - 拖拽或点击上传文件
   - 点击"开始分析"

3. 等待分析完成，自动跳转到结果页

### 测试历史记录

1. 点击顶部"地块管理分析"按钮
2. 查看历史记录列表
3. 点击"查看详情"查看结果
4. 点击"下载"下载报告文件

## 常见问题

### Q: 页面显示空白

**解决方案：**
1. 检查浏览器控制台是否有错误
2. 确认 Node.js 版本 >= 16
3. 删除 `node_modules` 重新安装：
   ```bash
   rm -rf node_modules
   npm install
   ```

### Q: API 调用失败

**解决方案：**
1. 检查后端服务是否启动
2. 检查 `.env` 中的 API 地址是否正确
3. 检查浏览器控制台的网络请求
4. 确认后端 CORS 配置正确

### Q: 文件上传失败

**解决方案：**
1. 检查文件格式是否正确
2. 检查文件大小是否超过限制
3. 检查后端是否正常接收文件

### Q: 历史记录不显示

**解决方案：**
1. 检查浏览器 localStorage 是否被禁用
2. 清除浏览器缓存后重试
3. 检查浏览器控制台是否有 JavaScript 错误

## 生产部署

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 部署到 Nginx

1. 将 `dist/` 目录内容复制到 Nginx 的 web 根目录

2. 配置 Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理（可选）
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. 重启 Nginx：

```bash
sudo nginx -s reload
```

### 部署到 Apache

1. 将 `dist/` 目录内容复制到 Apache 的 web 根目录

2. 创建 `.htaccess` 文件：

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

3. 重启 Apache：

```bash
sudo systemctl restart apache2
```

## 开发建议

### 推荐的开发工具

- **IDE**：VS Code
- **浏览器**：Chrome（带 Vue DevTools 扩展）
- **API 测试**：Postman 或 Insomnia

### VS Code 推荐扩展

- Volar（Vue 3 支持）
- ESLint
- Prettier
- Auto Rename Tag

### 开发流程

1. 修改代码
2. 保存文件（Vite 自动热更新）
3. 在浏览器中查看效果
4. 使用 Vue DevTools 调试

## 项目结构速览

```
my-project/
├── src/
│   ├── api/                    # API 服务
│   ├── components/             # 组件
│   ├── router/                 # 路由
│   ├── views/                  # 页面
│   ├── App.vue                 # 根组件
│   └── main.js                 # 入口
├── .env                        # 环境变量
├── package.json                # 依赖配置
└── vite.config.js              # Vite 配置
```

## 下一步

- 阅读 [README.md](README.md) 了解项目详情
- 阅读 [USER_GUIDE.md](USER_GUIDE.md) 了解用户使用流程
- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解架构设计

## 技术支持

如有问题，请查看：
1. 项目文档
2. 浏览器控制台错误信息
3. 后端 API 日志

---

祝您使用愉快！🎉
