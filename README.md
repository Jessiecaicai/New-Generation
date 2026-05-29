# Multi-Skill AI Agent

> 基于 ReAct 范式的可扩展 AI Agent 平台 —— 统一聊天入口,通过意图识别自动调度多个 Skill(NL2SQL 查询业务数据库 / 日志智能分析),架构支持插件化扩展新能力**无需改动核心代码**。

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-17-orange.svg)](https://www.oracle.com/java/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2-6DB33F.svg)](https://spring.io/projects/spring-boot)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-purple.svg)](https://www.langchain.com/)

---

## ✨ 项目特性

- 🧠 **真正的 Agent**:LLM 在 ReAct 循环里**自主决定**调用哪些工具,而不是代码硬编码顺序
- 🔌 **可插拔 Skill 框架**:自研 `BaseSkill` 抽象 + 自动发现机制,加新能力只需写一个类
- 🎯 **意图自动路由**:统一聊天框,Agent 根据用户问题自动切换工具集
- 🛡️ **NL2SQL 安全设计**:双层 SQL 校验(Python sqlparse + Java 执行层)+ 自纠错重试
- 🏗️ **异构服务架构**:Python(Agent 核心)+ Java(业务编排)双语言协作
- 📝 **Prompt 模板化**:YAML 管理,支持热加载

---

## 🚀 快速开始

### 环境依赖

- Python 3.11+
- Java 17+
- MySQL 8.0+
- Node.js 18+
- DeepSeek API Key([获取](https://platform.deepseek.com/api_keys))

### 启动步骤

```bash
# 1. 初始化数据库
mysql -uroot -p < docs/init.sql
mysql -uroot -p business_db < docs/sample-data.sql

# 2. 启动 Python Agent 服务
cd agent-python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "AGENT_DEEPSEEK_API_KEY=your_key_here" > .env
echo "AGENT_LLM_PROVIDER=deepseek" >> .env
uvicorn app.main:app --port 8001

# 3. 启动 Java 后端
cd agent-backend
mvn package -DskipTests
java -jar target/agent-backend-1.0.0.jar

# 4. 启动前端
cd agent-frontend
npm install
npm run dev
```

打开浏览器访问 [http://localhost:8000](http://localhost:8000)。

### 试着问几个问题

| 输入 | 自动走的 Skill |
|------|-------------|
| "销售额前 5 的客户" | NL2SQL → 生成 SQL + 数据表格 |
| "上个月每个产品类别的销售额" | NL2SQL → JOIN 查询 |
| "最近有什么 ERROR 日志" | LogAnalyzer → 分析报告 |
| "JAVA_BACKEND 模块有什么异常" | LogAnalyzer → 按模块过滤 |

---

## 🏛️ 架构总览

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React + Ant Design Pro)           │
│                     统一聊天框                            │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (同步)
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Java Spring Boot Backend (port 8080)        │
│                                                          │
│   ChatController(同步入口)                               │
│       └─ ChatOrchestrator                                │
│           ├─ SchemaService(查 information_schema)         │
│           ├─ AgentClientService(调用 Python)              │
│           └─ SqlExecutionService(SQL 双层校验 + 执行)     │
│                                                          │
│   双数据源: agent_meta(读写) + business_db(只读)         │
│   持久层: MyBatis-Plus                                   │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (POST /chat)
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Python FastAPI Agent Service (port 8001)      │
│                                                          │
│   ┌────────── AgentEngine 5 步流水线 ──────────┐        │
│   │  1. IntentRecognizer (LLM 分类)            │        │
│   │  2. SkillRegistry.get_skills_for_intent()  │        │
│   │  3. ContextAssembler (拼 Prompt)           │        │
│   │  4. AgentExecutor (ReAct 循环)             │        │
│   │  5. 解析输出 (抠 SQL)                       │        │
│   └────────────────────────────────────────────┘        │
│                                                          │
│   ┌─── 自研 Skill 框架 (BaseSkill + Registry) ───┐      │
│   │   ├─ NL2SqlSkill                              │      │
│   │   │     list_tables / lookup_schema /        │      │
│   │   │     sample_data / validate_sql           │      │
│   │   │                                          │      │
│   │   └─ LogAnalyzerSkill                         │      │
│   │         search_logs / get_error_stats /      │      │
│   │         get_log_context                      │      │
│   └──────────────────────────────────────────────┘      │
│                                                          │
│   PromptManager: YAML 模板化                            │
│   LLM: DeepSeek (OpenAI 协议兼容)                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   MySQL 8    │
                    │ ・business_db │  ← NL2SQL 查这个
                    │ ・system_logs │  ← LogAnalyzer 查这个
                    └──────────────┘
```

---

## 🧩 核心设计

### 1. AgentEngine 5 步流水线

一次对话的完整流程([agent_engine.py](agent-python/app/core/agent_engine.py)):

```
用户提问
  ↓
Step 1. 意图识别 (一次轻量 LLM 调用 → JSON)
  ↓ 结果: {"intent": "nl2sql", "confidence": 0.9}
  ↓
Step 2. Skill 路由 (SkillRegistry 按 intent_tags 筛选)
  ↓ 结果: [NL2SqlSkill] → 摊平成 4 个 Tool
  ↓
Step 3. Prompt 组装 (system + 意图专属 prompt + schema)
  ↓
Step 4. AgentExecutor (ReAct 循环, max_iterations=8)
  ↓ LLM 自主决策: lookup_schema → sample_data → 写 SQL → validate_sql
  ↓
Step 5. 输出解析 (正则抠出"标准 SQL"和"直观 SQL"两份)
```

### 2. 自研 Skill 框架

**为什么需要**:LangChain 没有"业务能力分组"概念,所有 tool 都是平铺的。Skill 是在 LangChain 之上加的**业务语义层**。

```python
class BaseSkill(ABC):
    name: str                  # 唯一标识
    description: str           # 给 LLM 看的能力描述
    intent_tags: list[str]     # 关联意图(路由依据)
    enabled: bool              # 整体启停开关

    @abstractmethod
    def get_tools(self) -> list[StructuredTool]:
        """返回该 Skill 提供的所有 LangChain Tool"""
```

**SkillRegistry 自动发现**:启动时扫描 `app/skills/builtin/` 和 `app/skills/custom/`,自动注册所有 `BaseSkill` 子类到全局表。

```python
@classmethod
def get_skills_for_intent(cls, intent: str) -> list[BaseSkill]:
    """意图路由:返回 intent_tags 包含该意图 且 enabled=True 的所有 Skill"""
    return [s for s in cls._skills.values()
            if intent in s.intent_tags and s.enabled]
```

**新增 Skill 只需 3 步**:
1. 在 `app/skills/builtin/` 下建目录
2. 写一个继承 `BaseSkill` 的类
3. 重启服务(或调 `/skills/reload` 接口热加载)

**核心代码不动一行**。

### 3. Prompt 工程

**约束 LLM 输出 JSON 的四个技巧**(意图识别):

```python
INTENT_SYSTEM_PROMPT = """你是一个意图分类器。   ← ① 明确角色

可选意图:                                         ← ② 列出有限选项
- nl2sql: 用户想查询数据库中的数据
- log_analysis: 用户想分析系统日志
- general: 一般性对话

请以 JSON 格式返回:{"intent": "xxx", "confidence": 0.9}   ← ③ 给完整样例
只返回 JSON,不要其他文字。"""                       ← ④ 压制解释欲
```

**代码兜底两道防线**:
- 剥掉 LLM 可能加的 markdown 包裹
- 解析失败默认走 general 意图

**Prompt 模板**全部抽到 [`app/prompts/templates/*.yaml`](agent-python/app/prompts/templates),支持热加载。

### 4. NL2SQL 双层安全防线

**Python 层**(`validate_sql` 工具):
- 用 sqlparse 检查仅 SELECT 语句
- 黑名单关键字过滤(DROP/DELETE/UPDATE/ALTER 等)
- 建议加 LIMIT 子句

**Java 层**(`SqlExecutionService`):
- 二次校验仅 SELECT
- 在 **只读数据源** 上执行(`business_db` 只配读权限)
- 执行失败时回传 `error_context` 触发 LLM **自纠错重试**(最多 3 次)

→ **Defense in Depth**(深度防御)思想。

### 5. 异构服务架构

**为什么用 Python + Java**:
- **Python**:LLM 生态成熟(LangChain),适合 Agent 核心逻辑
- **Java**:Spring Boot 成熟,适合业务编排、双数据源、安全校验、可观测性

**服务契约**:Java → Python 走 REST,关键字段:
- `intent_hint`:前端可强制覆盖意图识别
- `error_context`:SQL 执行失败时回传,触发自纠错

---

## 📁 目录结构

```
New-Generation/
├── agent-python/                  # FastAPI Agent 服务
│   └── app/
│       ├── core/                  # ⭐ Agent 核心
│       │   ├── agent_engine.py    # 5 步流水线
│       │   ├── intent_recognizer.py
│       │   └── context_assembler.py
│       ├── skills/                # ⭐ 自研 Skill 框架
│       │   ├── base.py            # BaseSkill 抽象基类
│       │   ├── __init__.py        # SkillRegistry 自动发现
│       │   └── builtin/
│       │       ├── nl2sql/        # NL2SQL Skill + 4 个工具
│       │       └── log_analyzer/  # LogAnalyzer Skill + 3 个工具
│       ├── prompts/               # YAML 模板管理
│       ├── routers/
│       └── models/
│
├── agent-backend/                 # Spring Boot 编排服务
│   └── src/main/java/com/newgen/agent/
│       ├── controller/            # ChatController(同步)/ Log / Schema / Skill
│       ├── service/
│       │   ├── ChatOrchestrator   # 编排 + 自纠错重试
│       │   ├── SchemaService      # 提取 information_schema
│       │   ├── SqlExecutionService # 双层 SQL 校验
│       │   └── ...
│       ├── config/                # MyBatisPlus / 双数据源 / Web
│       └── exception/
│
├── agent-frontend/                # React + Ant Design Pro
│   └── src/
│       ├── pages/Chat/            # 统一聊天页
│       ├── pages/LogMonitor/      # 日志监控
│       └── pages/AgentConfig/     # Skill / Prompt 配置
│
└── docs/
    ├── init.sql                   # 数据库初始化
    ├── sample-data.sql            # 示例业务数据
    └── interview-qa.md            # 面试问答整理
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|------|
| **前端** | React 18 · Ant Design Pro · Umi 4 · TypeScript |
| **后端编排** | Java 17 · Spring Boot 3.2 · MyBatis-Plus · Hikari · 双数据源 |
| **Agent 服务** | Python 3.11 · FastAPI · LangChain · DeepSeek API · Uvicorn |
| **持久化** | MySQL 8(utf8mb4) |
| **LLM** | DeepSeek-Chat(OpenAI 兼容协议) |
| **构建** | Maven · npm · venv |

---

## 📡 核心 API

### 对话(同步)

```bash
POST /api/chat
Content-Type: application/json

{
  "question": "销售额前 3 的客户",
  "sessionId": "test-1",
  "conversationHistory": []
}
```

返回:
```json
{
  "answer": "**标准 SQL**\n```sql\nSELECT...\n```",
  "intent": "nl2sql",
  "sql": "SELECT c.name, SUM(o.amount)...",
  "displaySql": "SELECT 客户名称, 销售总额...",
  "queryResults": {
    "columns": ["name", "total_amount"],
    "rows": [...],
    "rowCount": 3
  },
  "confidence": 0.9
}
```

### Skill 管理

```bash
GET  /api/skills              # 列出所有 Skill
PUT  /api/skills/{name}/toggle # 启用/禁用某 Skill
POST /api/agent/reload         # 热加载 Skill + Prompt
```

### 日志查询

```bash
GET /api/logs?level=ERROR&page=0&size=20
GET /api/logs/stats?hours=24
```

---

## 🎯 设计取舍

| 决策 | 选择 | 理由 |
|------|------|------|
| Agent 框架 | LangChain(`@tool` + AgentExecutor) | 省去手写 ReAct 循环 60+ 行 |
| 业务能力组织 | 自研 Skill 框架 | LangChain 没有 Skill 概念,加这层做意图路由和分组 |
| 调用方式 | Java → Python 同步 REST | 简单直观,适合 demo 规模 |
| 持久层 | MyBatis-Plus | 启动比 JPA 快(27s → 6s),SQL 可控 |
| 字符集 | MySQL utf8mb4 | LLM 输出含 emoji,utf8 存不下 4 字节 |
| LLM | DeepSeek | OpenAI 协议兼容、性价比高 |

---

## 🚧 已知限制 & 后续可扩展方向

- **暂不支持多轮 SQL 上下文记忆**(单轮 question 完整)
- **没有 RAG 知识库**(早期版本有,简化后移除以聚焦 Agent 核心)
- **意图识别用纯 prompt 引导**,可升级到 OpenAI Function Calling / Structured Outputs 提升可靠性
- **手撸 ReAct**可作为下一步重构方向,去除对 LangChain 的依赖
- **MCP server 化**:把 NL2SQL Skill 包装成独立 MCP server,开放给 Cursor/Claude Desktop 复用

---

## 📚 相关文档

- [示例 SQL 数据](docs/sample-data.sql) - 业务数据库初始化
- [数据库 Schema](docs/init.sql) - 元数据库表结构

---

## 📄 License

MIT © Jessie
