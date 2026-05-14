# AI 智能简历分析系统

基于 AI 大模型的智能简历解析与岗位匹配评分系统。支持 PDF 简历上传、关键信息提取、岗位匹配度分析，帮助招聘者快速筛选候选人。

## 项目架构

```
resume-analyzer/
├── backend/                 # Python 后端
│   ├── main.py              # FastAPI 入口，路由定义
│   ├── models.py            # Pydantic 数据模型
│   ├── parser.py            # PDF 解析与文本清洗 (PyMuPDF)
│   ├── extractor.py         # AI 关键信息提取
│   ├── matcher.py           # 简历-岗位匹配评分
│   ├── cache.py             # 缓存层 (Redis + 内存降级)
│   └── requirements.txt     # Python 依赖
├── frontend/                # 前端页面
│   ├── index.html           # 单页应用
│   ├── style.css            # 样式
│   └── app.js               # 交互逻辑
└── README.md
```

## 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 异步支持、自动生成 API 文档 |
| PDF 解析 | PyMuPDF (fitz) | 多页兼容、中文支持好 |
| AI 模型 | OpenAI 兼容 API | 支持通义千问、GLM、GPT 等任意兼容模型 |
| 缓存 | Redis + cachetools | Redis 优先，不可用时自动降级为内存缓存 |
| 前端 | 原生 HTML/CSS/JS | 零构建步骤，体积小 |

## 快速开始

### 1. 环境准备

- Python 3.10+
- （可选）Redis 服务

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 必选：AI 模型的 API Key
export OPENAI_API_KEY="your-api-key"

# 可选：自定义 API 地址和模型
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"

# 可选：Redis 缓存
export REDIS_URL="redis://localhost:6379/0"
```

**支持的 AI 服务商：**

| 服务商 | OPENAI_BASE_URL | 模型示例 |
|--------|-----------------|---------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |

### 4. 启动后端

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

### 5. 启动前端

```bash
cd frontend
python -m http.server 3000
```

访问 http://localhost:3000

或直接部署至 GitHub Pages（见下方部署说明）。

## API 文档

### `GET /api/v1/health`

健康检查。

**响应：**
```json
{ "status": "ok", "version": "1.0.0" }
```

### `POST /api/v1/resume/upload`

上传 PDF 简历并分析。

**请求：** `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | PDF 简历文件（最大 10MB） |
| job_description | string | 否 | 岗位需求描述，用于匹配评分 |



**响应：**
```json
{
  "success": true,
  "data": {
    "resume_id": "md5-hash",
    "raw_text": "清洗后的简历原文...",
    "basic_info": {
      "name": "张三",
      "phone": "13800138000",
      "email": "zhangsan@example.com",
      "address": "北京市海淀区"
    },
    "job_intent": {
      "position": "Python 后端工程师",
      "expected_salary": "15K-25K"
    },
    "background": {
      "work_years": "5年",
      "education": "本科 - 计算机科学",
      "projects": ["电商平台后端开发", "数据中台建设"]
    },
    "match_result": {
      "overall_score": 85,
      "skill_match_rate": 0.9,
      "experience_relevance": 0.8,
      "keywords_matched": ["Python", "FastAPI", "PostgreSQL"],
      "keywords_missing": ["Docker", "Kubernetes"],
      "analysis": "候选人具有良好的Python后端开发经验，与岗位需求匹配度较高..."
    }
  },
  "cached": false
}
```

## 部署

### 后端：阿里云函数计算 FC

1. 在阿里云 FC 控制台创建 Python 3.10 函数
2. 上传 `backend/` 目录代码
3. 配置环境变量 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 等
4. 配置 HTTP 触发器
5. 如需 Redis 缓存，开通云数据库 Redis 并配置 `REDIS_URL`

### 前端：GitHub Pages

1. Push 代码到 GitHub 仓库
2. 进入 Settings → Pages
3. Source 选择 GitHub Actions 或 Deploy from branch
4. 选择分支（如 `main`），目录选择 `/frontend`
5. 保存后等待部署完成
6. 修改 `app.js` 中的默认 API 地址为 FC 函数地址

## 核心设计说明

### 缓存策略

- **Key 设计**：`ra:{简历MD5}:{岗位描述MD5前8位}`
- **TTL**：24 小时
- **分层降级**：Redis → 内存 TTLCache，确保缓存层始终可用
- **响应标识**：`cached: true/false` 标识是否命中缓存

### AI 调用优化

- 信息提取和匹配评分各为独立的单次 LLM 调用
- Temperature 设为 0.1，确保输出稳定
- 每个 Prompt 限制简历文本最大 8000 字符，控制 Token 消耗
- Prompt 中要求严格 JSON 格式返回，便于程序解析

### 错误处理

- AI 服务不可用时降级返回空信息，不阻塞 PDF 解析
- 文件类型/大小前端+后端双重校验
- Redis 连接失败时自动切换内存缓存
- 网络异常在前端给出明确的用户提示

## License

MIT
