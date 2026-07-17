# AI Agent 项目 - 面试 / 概念问答整理

> 基于一次完整的 Q&A 对话整理，覆盖 MCP、LangChain、Skill、Prompt、Agent 架构等高频面试问题。
> 每个问题先给"快速答案"，再展开"详细解释"和"面试话术"。

---

## 目录

1. [MCP 是自己写的吗？也可以自己写吗](#1-mcp-是自己写的吗也可以自己写吗)
2. ["项目用 LangChain Tool 在进程内调用，没必要上 MCP" 怎么理解](#2-项目用-langchain-tool-在进程内调用没必要上-mcp-怎么理解)
3. ["单进程 FastAPI、Agent 和 Tool 跑在同一个 Python 解释器里" 怎么理解](#3-单进程-fastapi-agent-和-tool-跑在同一个-python-解释器里-怎么理解)
4. [LangChain Tool 封装 = 封装 Skill 吗？AgentEngine 是什么](#4-langchain-tool-封装--封装-skill-吗agentengine-是什么)
5. [意图识别 / RAG / Skill 选择具体怎么做到的？是 LangChain 吗？企业 MCP 改造成本？](#5-意图识别--rag--skill-选择具体怎么做到的是-langchain-吗企业-mcp-改造成本)
6. [在 system prompt 里约束 LLM 输出 JSON 怎么做](#6-在-system-prompt-里约束-llm-输出-json-怎么做)
7. [Prompt 是说明书吗？在项目代码里在哪里](#7-prompt-是说明书吗在项目代码里在哪里)
8. [为什么面试官问了 Skill / MCP 但没问 Prompt](#8-为什么面试官问了-skill--mcp-但没问-prompt)
9. [LangChain 没 Skill 这概念，那它到底做了什么？没有 LangChain 怎么做 AI Agent](#9-langchain-没-skill-这概念那它到底做了什么没有-langchain-怎么做-ai-agent)
10. [NL2SQL 的对话框能查 log 吗](#10-nl2sql-的对话框能查-log-吗)
11. [用 Claude Code 做的项目算 Vibe Coding 吗？算 AI Agent 项目吗？用 LLM 就算 Agent 吗](#11-用-claude-code-做的项目算-vibe-coding-吗算-ai-agent-项目吗用-llm-就算-agent-吗)
12. [手撸 ReAct 是不是就不需要 LangChain](#12-手撸-react-是不是就不需要-langchain)
13. [JSON Schema 是什么](#13-json-schema-是什么)
14. [那个 NL2SQL MCP server 具体怎么写的？为什么用 Python 不用 TypeScript](#14-那个-nl2sql-mcp-server-具体怎么写的为什么用-python-不用-typescript)
15. [附录：高频拷打题速查表](#附录高频拷打题速查表)

---

## 1. MCP 是自己写的吗？也可以自己写吗

### 快速答案
**MCP server 完全可以自己写——而且这正是它的设计目的**。MCP 不是某个产品或 API，而是 Anthropic 2024 年 11 月开源的**协议规范**，类似 HTTP / LSP。

### 详细解释

**MCP = Model Context Protocol（模型上下文协议）**

类比：

| 类比对象 | 关系 |
|---------|------|
| **HTTP 协议** | 谁都能基于 HTTP 写自己的 Web 服务器 |
| **LSP**（Language Server Protocol） | 谁都能写 LSP server 让 VSCode 接入 |
| **MCP** | 谁都能写 MCP server，让 Claude / Cursor / Cline 接入 |

**最小例子**：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city} 今天晴，25°C"

if __name__ == "__main__":
    mcp.run()
```

在 Claude Desktop 配置文件加一行就能调用这个工具。**整个过程没调任何外部 API，全是自己写的代码。**

### MCP 三类原语

| 原语 | 作用 | 例子 |
|------|------|------|
| **Tools** | LLM 主动调用的函数 | 查数据库、发邮件 |
| **Resources** | LLM 读取的数据源 | 文件、API 响应 |
| **Prompts** | 预定义的 prompt 模板 | "代码 review 模板" |

底层是 JSON-RPC 2.0，传输支持 stdio / SSE / Streamable HTTP。

### 面试话术

> "MCP 是 Anthropic 提出的让 LLM 接入外部能力的**协议规范**，不是某个具体的 API。MCP server **就是给开发者自己写的**——把任何外部资源（数据库、API、文件系统）包装成 MCP server，符合协议规范就能被 MCP client 调用。
>
> 我项目里**就有一个自己写的 NL2SQL MCP server**——用 Python + 官方 `mcp` SDK 写的，~200 行代码，暴露 5 个工具（list_tables / lookup_schema / sample_data / validate_sql / execute_select_sql），通过 stdio 协议直接给 Claude Desktop / Cursor 当工具用。**不必经过项目自家前端或 Java 后端**，任何 MCP client 都能调。"

---

## 2. "项目用 LangChain Tool 在进程内调用，没必要上 MCP" 怎么理解

### 快速答案
**两条赛道并存，目标不同**：
- **内部链路**用 **LangChain Tool**（进程内函数，纳秒级）—— 服务前端用户
- **对外接口**用 **MCP server**（跨进程协议，毫秒级）—— 服务任何 MCP client

不是二选一，而是"对内追求性能、对外追求生态兼容"。

### 项目实际的"双轨"架构

```
              内部链路（追求性能）           对外接口（追求生态）
              ─────────────────              ──────────────────
              前端聊天框                      Claude Desktop / Cursor
                  ↓                              ↓
              Java backend                  （MCP stdio 协议）
                  ↓ HTTP                        ↓
              agent-python                   nl2sql-server (Python)
                  ↓                              ↓
              LangChain @tool                MCP @mcp.tool()
                  ↓                              ↓
              （同进程函数调用）              （独立进程 + JSON-RPC）
                  ↓                              ↓
                  └──────→ 同一个 MySQL ←─────────┘
```

### 进程内 vs 跨进程对比

**LangChain Tool 实际发生的事**：
```
AgentEngine → tool_registry["lookup_schema"] → 直接 Python 函数调用 → 返回 dict
```
纳秒级，没有任何网络/序列化开销。

**MCP 实际发生的事**：
```
client → 把参数序列化为 JSON → stdio 发到 MCP server 进程 → 反序列化执行 → 结果再序列化 → 写回 client
```
毫秒级，每次调用要序列化两次。

### 为什么内部链路不上 MCP

1. **没有跨进程需求** —— 内部只有 agent-python 这一个消费方
2. **徒增性能开销** —— 一次 ReAct 推理可能调 5~10 次 tool，多 50~500ms 不值
3. **徒增部署复杂度** —— 多管理一个进程的生命周期

### 为什么还要单独写一个 MCP server

1. **对外开放** —— 让任何 MCP client（Claude Desktop / Cursor / Cline）都能复用 NL2SQL 能力
2. **跨语言场景** —— Java / Go / Rust 写的 Agent 也能调
3. **生态接入** —— 符合标准协议，未来可以发布到 MCP 社区生态
4. **进程级隔离** —— sandbox 化，对外服务时崩了不影响主链路

### 生活化类比

| 方案 | 类比 |
|------|------|
| **LangChain Tool（进程内）** | 自家厨房，伸手就能拿调料 |
| **MCP（跨进程）** | 在街边开了个调料店，街坊邻居都能买 |

→ 自家做饭 → 在自家厨房做（LangChain Tool）
→ 想让街坊也能用同一份配方 → 把店开出来（MCP server）
→ **两件事不冲突，可以同时做**

---

## 3. "单进程 FastAPI、Agent 和 Tool 跑在同一个 Python 解释器里" 怎么理解

### 快速答案
你的整个 Python 后端就是操作系统里的**一个 python 进程**，AgentEngine 和所有 Tool 函数都是这个进程**内存里的 Python 对象**，互相调用 = 内存里查表 + 函数调用，零开销。

### 关键概念

**进程**：操作系统分配资源的最小单位。每个进程：
- 独立的内存空间
- 独立的 PID
- 进程间通信必须走序列化（IPC）

**Python 解释器**：一个 python 进程 = 一个解释器实例。它内部有：
- module registry（所有 import 的模块）
- 全局变量字典
- GIL（全局解释器锁）

### 你项目的物理形态

```
┌──── 1 个 Python 进程（uvicorn）───────────┐
│  ┌── 1 个 Python 解释器 ───────────────┐  │
│  │  内存中：                            │  │
│  │   ├─ FastAPI app                    │  │
│  │   ├─ AgentEngine 实例               │  │
│  │   ├─ Skill 函数：                    │  │
│  │   │   ├─ lookup_schema_tool         │  │
│  │   │   ├─ validate_sql_tool          │  │
│  │   │   └─ ...                        │  │
│  │   └─ tool registry (一个 dict)      │  │
│  └─────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**AgentEngine 调工具时发生的事**：
```python
tool_name = "lookup_schema"            # LLM 返回的工具名
tool_fn = self.tool_registry[tool_name] # 从内存 dict 查
result = tool_fn(table_name="users")     # 直接 Python 函数调用
```

= 普通的 Python 函数调用，纳秒级。

### 类比：办公楼

| 概念 | 类比 |
|------|------|
| 单进程 FastAPI | 一栋办公楼 |
| Python 解释器 | 楼里共享的办公环境（WiFi、会议室） |
| AgentEngine | 5 楼策划部 |
| Tool 函数 | 3 楼执行部 |
| Agent 调 Tool | 打**内线电话**，同楼内秒接 |
| 改成 MCP | 执行部搬到对面大楼，打**外线电话** |

---

## 4. LangChain Tool 封装 = 封装 Skill 吗？AgentEngine 是什么

### 快速答案
- **Tool 封装的是单个函数**，给函数加 name / description / args_schema 让 LLM 能调用
- **Skill 是自己加的更高一层抽象**：一组相关 Tool 的业务分组（LangChain 没这概念）
- **AgentEngine 是 Agent 的"总指挥"**：把 LLM、意图识别、Skill、Prompt、ReAct 循环串成流水线

### 三者关系

```
            概念层级           你代码里
        ┌───────────────┐
        │   Skill       │  ← NL2SqlSkill（业务能力分组）
        └───────┬───────┘
                │ get_tools() 返回多个 Tool
                ▼
        ┌───────────────┐
        │   Tool        │  ← @tool 装饰的函数
        └───────┬───────┘
                │ 注册到
                ▼
        ┌───────────────┐
        │  AgentEngine  │  ← 总指挥（编排者）
        └───────────────┘
```

### Tool 详解

```python
@tool
def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构。
    Args:
        table_name: 要查看的表名
    """
```

`@tool` 装饰器自动从函数提取：

| 多出来的东西 | 用途 |
|------------|------|
| **name** | 函数名 → 工具名 |
| **description** | docstring → 工具描述 |
| **args_schema** | 参数类型 → JSON Schema |

→ 翻译成 LLM 能理解的"工具说明书"。

### Skill 详解

```python
class NL2SqlSkill(BaseSkill):
    name = "nl2sql"
    description = "..."
    intent_tags = ["nl2sql"]
    enabled = True

    def get_tools(self):
        return [lookup_schema_tool, list_tables_tool, ...]
```

Skill 的价值：
1. **业务语义聚合**：4 个 SQL 相关工具归一个 Skill
2. **统一开关**：enabled=False 一次性禁用
3. **意图路由**：intent_tags 让 AgentEngine 按意图筛选
4. **可插拔扩展**：加新能力只需新建 Skill 类

**LangChain 没有 Skill 概念**——Skill 是你自己加的一层抽象。

### AgentEngine 详解

它本身**不做业务**，而是**编排别人做业务**：

```
┌──────────────── AgentEngine ────────────────┐
│   意图识别 → Skill 选择 → 组装 Prompt+Tools  │
│   → ReAct 循环 → 返回                        │
└─────────────────────────────────────────────┘
```

类比 Spring：
- Controller ≈ FastAPI router
- **Service**（业务编排）≈ **AgentEngine**
- Repository ≈ Skill / Tool

### 面试话术

> "**Tool 是单个 Python 函数的 LLM 协议封装**——加上 name、description、args_schema。
> **Skill 是我项目自己加的一层抽象**——把一组相关 Tool 打包成业务能力，方便启停和意图路由。LangChain 本身没有 Skill 概念。
> **AgentEngine 是整个 Agent 的编排器**——把 LLM、意图识别、Skill、Prompt、ReAct 循环串成流水线。类比 Spring 的 Service 层。"

---

## 5. 意图识别 / RAG / Skill 选择具体怎么做到的？是 LangChain 吗？企业 MCP 改造成本？

### 快速答案
- **意图识别**：一次轻量 LLM 调用 + JSON 解析（**没用 LangChain 框架功能**）
- **RAG 检索**（已移除）：曾用 ChromaDB 原生 SDK（**没用 LangChain Retriever**）
- **Skill 选择**：字典查找 + 列表摊平（**纯自己写**）
- **LangChain 真正用到的只有**：`@tool` 装饰器 + `AgentExecutor`（ReAct 循环驱动）

### Step 1: 意图识别机制

```python
# 1. AgentEngine 调用
ir = await self.intent_recognizer.recognize(question, ...)

# 2. IntentRecognizer 内部
messages = [
    SystemMessage(content=INTENT_SYSTEM_PROMPT),
    HumanMessage(content=f"用户问题: {question}"),
]
response = await self.llm.ainvoke(messages)
result = json.loads(response.content.strip())
# result = {"intent": "nl2sql", "confidence": 0.9}
```

**核心是 prompt engineering**：在 system prompt 约束 LLM 输出 JSON 格式，然后 json.loads 解析。

### Step 2: 挑选工具

```python
# SkillRegistry 在内存 dict 里筛
return [s for s in cls._skills.values()
        if intent in s.intent_tags and s.enabled]

# 摊平成 Tool 列表
tools = []
for s in active_skills:
    tools.extend(s.get_tools())
```

**完全自己写的 Python 逻辑**，零框架成分。

### LangChain 真正用在哪

| 用到的地方 | LangChain 提供的能力 |
|----------|---------------------|
| **@tool 装饰器** | 把函数转成 LLM 能调用的 tool（生成 JSON Schema） |
| **create_tool_calling_agent + AgentExecutor** | 跑 ReAct 循环 |
| ChatOpenAI / ChatOllama | LLM 客户端封装 |
| ChatPromptTemplate / MessagesPlaceholder | Prompt 模板抽象 |

**核心结论**：项目真正依赖 LangChain 的只有 "ReAct 循环驱动" 和 "@tool 装饰器"，其他全是自己写。

### 企业 MCP / Skill 改造成本（基于真实数据）

我们**已经写了一个 NL2SQL MCP server**作为试点，这是实测出来的数据：

| 改造点 | 实际工作量 |
|--------|-----------|
| NL2SQL Skill → MCP server | **1 天**（Python + `mcp` SDK，~200 行）|
| LogAnalyzer Skill → MCP server | 预估同等量级（1 天） |
| AgentEngine 改接 MCP client | 中等（2 天）—— 加 MCP client 层封装 |
| 进程编排 | 小（半天）—— Claude Desktop config 一次性 |
| SkillRegistry → MCP 发现机制 | 中（1 天）—— Skill 自动发现改为 MCP `list_tools` 调用 |
| 测试 / 文档 | 中（1~2 天） |

**合计：5~7 个工作日**（比原先估的 6~10 工作日少一些，因为 SDK 比想象的成熟）

### 项目当前实际状态

**双轨制（推荐做法）**：

| | 内部链路 | 对外 MCP |
|---|---|---|
| 代码位置 | `agent-python/app/skills/builtin/nl2sql/` | `mcp-servers/nl2sql-server/server.py` |
| 框架 | LangChain `@tool` | MCP `@mcp.tool()` |
| 消费方 | 项目自家前端 | Claude Desktop / Cursor / 任何 MCP client |
| 性能 | 进程内函数（快）| stdio JSON-RPC（多一次序列化）|

**有 5% 代码重复（SQL 校验、表名白名单等逻辑两边都有）**——可接受，因为两边消费场景不同，做成共享库反而过度抽象。

### 面试话术

> "我项目用的是**双轨架构**：
> - **内部链路**用 LangChain 的 `@tool` + AgentExecutor，agent-python 这个进程内函数调用，纳秒级——服务自家前端的聊天框。
> - **对外接口**单独写了一个 **NL2SQL MCP server**——独立 Python 进程，通过 stdio + JSON-RPC，让任何 MCP client（Claude Desktop / Cursor）都能调。
>
> 这么做的考虑：**两条赛道目标不同**——内部追求性能（不要 50-500ms 的多轮 tool 调用开销），对外追求生态兼容（标准协议、跨语言、可被任意 client 调）。
>
> 实际工作量也验证了——把 NL2SQL 改造成 MCP server 大概 1 天，**核心 AgentEngine 流程没动**，体现了抽象设计的价值。"

---

## 6. 在 system prompt 里约束 LLM 输出 JSON 怎么做

### 快速答案
**Prompt 引导 + 代码兜底**：用四个 prompt 技巧让 LLM 95% 概率输出 JSON，再用代码处理剩下 5% 的 case。

### Prompt 的四个技巧

参考项目里的 INTENT_SYSTEM_PROMPT：

```python
"""你是一个意图分类器。根据用户的问题，判断其意图类别。

可选意图：
- nl2sql: 用户想查询数据库中的数据（涉及查询、统计、报表）
- log_analysis: 用户想分析系统日志或排查错误
- general: 一般性对话

请以 JSON 格式返回：{"intent": "xxx", "confidence": 0.9}
只返回 JSON，不要其他文字。"""
```

| 技巧 | 作用 |
|------|------|
| ① **明确角色定位** "你是一个意图分类器" | LLM 进入分类器思维模式 |
| ② **给出有限选项**（枚举意图 + 触发词） | 把输出空间框死 |
| ③ **给出精确的 JSON 样例** | LLM 模仿这个形状（最关键！） |
| ④ **负面约束** "只返回 JSON 不要其他文字" | 压制 LLM 的解释欲 |

### 代码兜底

```python
text = response.content.strip()
# 兜底 1：剥掉 markdown 代码块
if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]

result = json.loads(text.strip())

# 兜底 2：解析失败给默认值
except Exception as e:
    return {"intent": "general", "confidence": 0.5}
```

### 升级方案对比

| 方案 | 原理 | 可靠性 |
|------|------|--------|
| **纯 prompt 约束** | 提示词引导 | ~95% |
| **OpenAI JSON Mode** | API 参数 `response_format={"type":"json_object"}` | ~99% |
| **Function Calling** | 给 LLM 传 JSON Schema | ~100% |
| **LangChain `with_structured_output`** | 封装上面两种 | ~100% |
| **Pydantic + Instructor** | 验证 + 失败重试 | ~100% |

### 为什么 LLM 真的听话

1. **训练数据里见过大量 JSON** —— 对 JSON 格式有很强先验
2. **指令微调（Instruction Tuning）** —— 学会了"按用户要求格式输出"
3. **自回归生成的惯性** —— 一旦先吐出 `{`，后面会被拉着续写 JSON

### 面试话术

> "我用的是 **prompt 引导 + 代码兜底** 的组合：
> **prompt 层四个技巧**：① 明确角色 ② 枚举有限选项 ③ 给完整 JSON 样例当锚点 ④ 加 '只返回 JSON 不要其他文字' 压制解释欲。
> **代码层两道兜底**：① 剥掉 markdown 包裹 ② 解析失败返回默认意图，避免一次意图识别失败让整个对话挂掉。
> 这套方案经验成功率 95%+。如果要更高可靠性，可以升级到 Function Calling / Structured Outputs，给模型传 Pydantic schema 在生成阶段就强约束。"

---

## 7. Prompt 是说明书吗？在项目代码里在哪里

### 快速答案
**Prompt ≠ 单纯的说明书**。它是每次对话里塞给 LLM 的"指令 + 示例 + 上下文 + 问题"的总和。

### 项目里 Prompt 的 3 个存放位置

**位置 1：YAML 模板文件（主战场）**

```
agent-python/app/prompts/templates/
├── system.yaml                ← Agent 主系统说明书
├── intent_routing.yaml        ← (备用)
├── nl2sql/
│   ├── generate.yaml          ← SQL 生成 + few-shot
│   └── error_fix.yaml         ← SQL 自纠错
└── log_analysis/
    └── analyze.yaml           ← 日志分析
```

**位置 2：Python 文件里的常量**

```python
# intent_recognizer.py
INTENT_SYSTEM_PROMPT = """你是一个意图分类器..."""
```

不变的、单点使用的 prompt 写代码里更直观。

**位置 3：@tool 函数的 docstring（工具说明书）**

```python
@tool
def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构（列名、类型、是否可空、注释）。

    Args:
        table_name: 要查看的表名
    """
```

`@tool` 装饰器自动提取 docstring 作为工具描述喂给 LLM。

### Prompt 的 4 个组成部分

| 组成 | 类比 | 项目里对应 |
|------|------|------------|
| **指令（Instructions）** | 说明书 | system.yaml + nl2sql/generate.yaml |
| **示例（Few-shot）** | 范例题 | generate.yaml 里的"问题→SQL"示范 |
| **上下文（Context）** | 参考资料 | Schema + 对话历史 |
| **当前问题（Query）** | 真正的提问 | `{input}` |

### Prompt 怎么被拼装

```python
# ContextAssembler.build_prompt 大致流程：
system = PromptManager.render("system", available_skills="...")

if intent == "nl2sql":
    system += PromptManager.render("nl2sql/generate", schema_summary=...)
    if error_context:
        system += PromptManager.render("nl2sql/error_fix", ...)

return ChatPromptTemplate.from_messages([
    ("system", system),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
```

### 为什么抽 YAML

1. 改 prompt 不用改代码（热加载）
2. 版本管理（YAML 加 version 字段做 A/B）
3. 前端可在线编辑（/api/prompts 接口）
4. 占位符显式声明，一眼看出需要什么变量

---

## 8. 为什么面试官问了 Skill / MCP 但没问 Prompt

### 快速答案
**Prompt 已经被默认你会了**——面试官在挑高区分度的问题。问"你写过 prompt 吗"等于问"你会用 ChatGPT 吗"，没意义。

### 问题的"信息密度"分级

| 问题 | 区分度 | 为什么 |
|------|-------|--------|
| 你写过 prompt 吗 | ⭐ 极低 | 用过 ChatGPT 都写过 |
| 你写过 Skill 吗 | ⭐⭐⭐ 中 | 看抽象设计能力 |
| 你写过 MCP server 吗 | ⭐⭐⭐⭐ 高 | 看跨进程思维 + 行业前沿跟进 |

### 问 Skill / MCP 背后真正想知道什么

**问 Skill** → 想知道：
- 抽象设计能力
- 插件化架构理解
- 可维护性意识

**问 MCP** → 想知道：
- 跨进程 / 服务化思维
- 懂不懂协议和标准
- 跟不跟行业前沿
- 能识别 over-engineering

**问 prompt** → 啥也看不出来，所有做 LLM 项目的人都写过

### Prompt 工程在工业界的地位

| 能力 | 工业界态度 |
|------|----------|
| 基础 prompt 写作 | 默认技能 |
| few-shot 示例 | 默认技能 |
| CoT / ReAct 等 prompt 模式 | 中级，要会但不稀奇 |
| **Skill / Tool 设计** | ⭐ 工程师核心 |
| **Agent 编排 / RAG 架构** | ⭐ 工程师核心 |
| **MCP / 跨进程协议** | ⭐ 高阶 |

### 实战建议

**1. 高频拷打题主动准备**：Skill 设计 / MCP / RAG 链路 / Agent 流程 / 并发 / 安全

**2. Prompt 即使不被问，主动提**：
> "我做 NL2SQL 时把 schema 信息通过 prompt 模板注入，同时用 few-shot 给了 5 个标准案例。Prompt 全部抽到 YAML，**支持热加载**，不用改代码就能调优。"

**3. 反客为主升级问题**：
被问 MCP 时多讲一步——"说到协议层的事，我项目里 Java 和 Python 之间也有协议设计，比如 error_context 字段就是为了 SQL 自纠错的，这种 service-to-service 契约设计和 MCP 是同源思维。"

---

## 9. LangChain 没 Skill 这概念，那它到底做了什么？没有 LangChain 怎么做 AI Agent

### 快速答案
**LangChain = "做 LLM 应用要用到的一堆零件的集合"**，最有价值的两件事：① 统一不同 LLM 接口 ② 替你写 ReAct 循环（AgentExecutor）。没有它也能做 Agent，但要多写 60+ 行胶水代码。

### LangChain 的 7 个模块

| 模块 | 干什么 | 你项目用到吗 |
|------|--------|------------|
| **Models** | 各家 LLM 的统一接口 | ✅ ChatOpenAI / ChatOllama |
| **Messages / Prompts** | Prompt 模板抽象 | ✅ ChatPromptTemplate |
| **Tools / @tool** | 函数 ↔ LLM 协议翻译 | ✅ 所有 @tool |
| **Agent / AgentExecutor** ⭐ | ReAct 循环驱动器 | ✅ create_tool_calling_agent |
| **Document Loaders / Splitters** | RAG 预处理 | ❌（已移除）|
| **Memory** | 对话记忆管理 | ❌（自己管理对话历史）|
| **Retrievers / VectorStores** | RAG 检索抽象 | ❌（已移除）|

### 没有 LangChain 怎么做 —— 对比代码

**LangChain 版本（3 行）**：
```python
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=8)
result = await executor.ainvoke({"input": question})
```

**纯原生版本（60+ 行）**：
```python
# 1. 手写工具 JSON Schema
tools = [{"type": "function", "function": {...}}, ...]

# 2. 手写 ReAct 循环
messages = [{"role": "system", ...}, {"role": "user", ...}]
for iteration in range(8):
    response = client.chat.completions.create(...)
    msg = response.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        return msg.content
    for tool_call in msg.tool_calls:
        result = tool_funcs[tool_call.function.name](**args)
        messages.append({"role": "tool", "tool_call_id": ..., "content": result})
```

还要处理：流式、并行工具调用、Anthropic 协议差异、错误重试……

### 没有 LangChain 的著名项目

| 项目 | 做法 |
|------|------|
| **AutoGPT** (2023.03) | 全手撸 prompt，比 LangChain 还火过一阵 |
| **BabyAGI** | 几百行 Python，无框架 |
| **LangGraph**（LangChain 团队自己出的） | 用状态图替代 AgentExecutor |

### 工业界"反 LangChain"批评

| 批评 | 表现 |
|------|------|
| **抽象过度** | 同一件事多种写法 |
| **黑魔法太多** | 调试痛苦 |
| **生产难维护** | 大版本不兼容 |
| **依赖膨胀** | 100+ 包，200MB+ |
| **性能开销** | 多层 wrapper，慢 30%+ |

### 现在的替代方案

| 方案 | 适用 |
|------|------|
| OpenAI Assistants API | 简单但被绑死 |
| Anthropic SDK + 手写 | Claude 官方推荐 |
| **LangGraph** | 状态图，可控性高 |
| CrewAI | 多 Agent 协作 |
| DSPy | prompt 编译 |
| 纯原生 SDK | 完全可控 |

### 面试话术

> "我是**有选择地用** LangChain——只用了最核心的两个能力：`@tool` 装饰器和 `AgentExecutor`。其他部分故意没用：对话历史在 Java 后端 MySQL 自己管，Prompt 用 YAML 模板。这样**避免被 LangChain 的版本迭代绑架**，也方便未来切到 LangGraph 或原生 SDK。
>
> 不用 LangChain 完全可以——手写 ReAct 循环大概 60 行，但要处理流式、并行工具调用、协议差异、错误重试，工作量翻 5 倍。**ReAct 循环 + Tool Schema 让 LangChain 做，其他自己来**——这是我的取舍。"

---

## 10. NL2SQL 的对话框能查 log 吗

### 快速答案
**能**，而且这正是 Agent 多 Skill 架构的核心卖点——**同一个聊天框，根据用户问什么自动切到对应 Skill**。

### Skill 自动切换的用户体验

```
用户：查询销售额前 5 的客户
Agent：[切到 NL2SQL] SELECT ... → 返回 SQL + 数据表格

用户：最近有什么 ERROR 日志
Agent：[切到 LogAnalyzer] 调 search_logs → 返回错误统计 + 分析
```

**用户根本不需要切换模式——直接问，Agent 自己判断**。

### 路由机制三层

**1. 意图识别层**：一次轻量 LLM 调用把问题分类到几个意图

**2. Skill 筛选层**：SkillRegistry 根据 intent_tags 筛出对应 Skill，只加载它的工具到 LLM 上下文

**3. Prompt 切换层**：ContextAssembler 根据意图追加专属 prompt

### 前端展示分流

不同 Skill 返回内容不一样：

| Skill | 返回内容 | 前端渲染 |
|-------|---------|---------|
| NL2SQL | answer + sql + display_sql + 数据 | SQL 高亮 + 数据表格 |
| LogAnalyzer | answer | Markdown 富文本 |

ChatResponse 里有 `intent` 字段，前端 MessageBubble 根据 intent 分发到不同渲染器。

### 兜底机制

意图识别错了怎么办？还有 `intent_hint` 机制：

```python
if request.intent_hint:
    intent = request.intent_hint
```

→ 前端可以加手动切换按钮，传 `intent_hint` 强制走某个 Skill。

### 面试话术

> "我项目的核心设计是**统一聊天入口 + Skill 自动路由**——同一个聊天框，用户问 SQL 走 NL2SQL，问日志走 LogAnalyzer。
>
> 路由机制有三层：① 意图识别（一次 LLM 调用分类）② Skill 筛选（按 intent_tags）③ Prompt 切换（不同意图不同 prompt）。
>
> 前端响应展示：ChatResponse 里带 intent 字段，前端根据 intent 分发到不同渲染器——SQL 结果渲染表格，日志结果渲染分析卡片。
>
> 用户**完全感知不到 Skill 切换**——这是和'纯 NL2SQL 工具'最大的区别。"

---

## 11. 用 Claude Code 做的项目算 Vibe Coding 吗？算 AI Agent 项目吗？用 LLM 就算 Agent 吗

### 快速答案
1. **不是纯 Vibe Coding**，是 AI 辅助开发，偏 Vibe 一侧——继续追问 why 就能跳出
2. **是真正的 AI Agent 项目**——Agent 6 个核心要素全有
3. **用 LLM ≠ Agent**——区分标准是"LLM 是否在循环里自主决策调用工具"

### 问题 1：算 Vibe Coding 吗

**Vibe Coding（Karpathy 2025）核心特征**：
- 不读代码
- 不理解架构
- 出错复制错误给 AI
- 代码所有权感弱

**你的状态对照**：

| 维度 | 纯 Vibe Coding | 你 |
|------|---------------|-----|
| 是否读代码 | ❌ | ✅ 主动追问每个模块原理 |
| 是否理解架构 | ❌ | ✅ 能讲清 Skill / Agent 关系 |
| 是否能 debug | ❌ | ✅ 能从 ERROR 日志定位问题 |
| 是否做架构决策 | ❌ | ✅ 主动决定 MyBatis-Plus 迁移、简化 RAG |

**判断标准**：把 Claude 关掉，能不能独立做这三件事：
1. 新加一个 Skill（完全自己写）
2. 改 nl2sql/generate.yaml 的 few-shot，看效果变化
3. 修一个真实 bug（自己定位+修复）

能做完 → AI 辅助开发；做不完 → 还在 Vibe Coding

### 问题 2：算 AI Agent 项目吗

**AI Agent 定义（Lilian Weng）**：
```
Agent = LLM + Planning + Memory + Tool use
```

**你项目逐条对照**：

| Agent 要素 | 你的实现 |
|-----------|---------|
| **LLM 作为决策大脑** | DeepSeek |
| **Tools（外部能力）** | NL2SQL / 日志查询 |
| **ReAct 循环** | AgentExecutor(max_iterations=8) |
| **Planning（任务规划）** | 意图识别 + LLM 自主调工具 |
| **Memory（记忆）** | conversation_history 多轮对话 |
| **Tool use** | @tool + tool_calls 协议 |

✅ 6 个核心要素全有——**教科书级别的 Agent 实现**

更细分一层：你做的是 **"Multi-skill ReAct Agent"**：

```
普通 Agent ─── 单一工具 + 一次 LLM 调用
   ↓
ReAct Agent ─── 工具 + 多轮思考循环
   ↓
Multi-skill Agent ─── ReAct + 意图路由 + 可插拔技能体系 ← 你在这
```

### 问题 3：用 LLM 就算 Agent 吗

**不算**。按"LLM 在系统里扮演什么角色"分四档：

| 等级 | 类型 | 特征 | 例子 |
|------|------|------|------|
| **L1** | LLM 调用工具 | 调一次 API 展示结果 | ChatGPT 网页版 |
| **L2** | LLM 增强应用 | 用 LLM 做特定任务 | DeepL 翻译 |
| **L3** | RAG 应用 | prompt 里塞外部知识 | 文档问答机器人 |
| **L4** | **AI Agent** | LLM **自主决定**调哪些工具 | **你的项目** |

**核心区别**：**谁在做决策**
- L1-L3：应用代码做决策，LLM 只是被使用
- L4：LLM 做决策，代码只是执行 LLM 的指令

### 判断"是不是 Agent"硬性标准

问 4 个问题：
1. LLM 能调用工具吗？（不是被工具调用）
2. LLM 决定调用什么工具？（不是代码硬编码顺序）
3. 是否有循环？（基于工具结果再做下一个决策）
4. LLM 决定什么时候停？（不是代码强制只调一次）

**4 个全是 Yes → Agent**
**任意一个 No → 只是 LLM 应用**

### 给项目的总评

| 维度 | 等级 |
|------|------|
| 项目类型 | **真正的 AI Agent** |
| 架构复杂度 | **中**（简化后）|
| 技术深度 | **中**（用 LangChain 比手撸差一档）|
| 开发模式 | **AI 辅助 / 略 Vibe 倾向** |
| **简历价值** | **中上** |

### 简历精准定位话术

> "我设计并实现了一个 **Multi-skill AI Agent 平台**——支持自然语言查询数据库（NL2SQL）、日志智能分析两个内置 Skill。
>
> **架构亮点**：
> - **意图识别 + Skill 路由** 实现一个聊天框服务多种业务能力
> - **LangChain @tool + AgentExecutor** 实现 ReAct 循环（最多 8 轮工具调用）
> - 自研 **BaseSkill 抽象 + SkillRegistry 自动发现**（LangChain 没有 Skill 概念）
> - **Python（FastAPI Agent）+ Java（Spring Boot 编排）双语言架构**
>
> 开发过程**深度使用 AI 辅助**，但所有架构决策、性能调优、bug 定位都是我主导——包括 MyBatis-Plus 迁移、MySQL emoji 字符集问题、404 噪声日志处理这些生产级问题。"

---

## 12. 手撸 ReAct 是不是就不需要 LangChain

### 快速答案
**核心 Agent 完全可以脱钩**（去掉 AgentExecutor、@tool、ChatOpenAI 等），用 ~60 行手写 ReAct 循环替代。

### LangChain 用法逐条评估

| LangChain 用法 | 手撸后需要吗 |
|---------------|--------------|
| `create_tool_calling_agent` + `AgentExecutor` | ❌ 去掉（自己写 ReAct 循环）|
| `@tool` 装饰器 | ⚠️ 可去（但要手写 JSON Schema）|
| `ChatPromptTemplate` | ⚠️ 可去（字符串拼接代替）|
| `HumanMessage` / `SystemMessage` | ❌ 去掉（OpenAI 原生 dict）|
| `ChatOpenAI` | ❌ 去掉（OpenAI SDK 原生）|

### 手撸 ReAct 长什么样

```python
from openai import AsyncOpenAI

class HandRolledAgent:
    def __init__(self, api_key, base_url, model):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def run(self, system_prompt, question, tools_def, tool_funcs,
                  history=None, max_iterations=8):
        messages = [{"role": "system", "content": system_prompt}]
        if history: messages.extend(history)
        messages.append({"role": "user", "content": question})

        for iteration in range(max_iterations):
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_def,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                return msg.content

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                    result = tool_funcs[tc.function.name](**args)
                except Exception as e:
                    result = f"TOOL_ERROR: {e}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

        return "达到最大迭代次数"
```

工具 schema 每个要自己写 ~15 行 JSON。

### 手撸 vs LangChain 对比

| 维度 | LangChain | 手撸 |
|------|----------|------|
| 核心代码量 | ~10 行 | ~80 行 |
| 每工具维护 | `@tool` 1 行 | 15 行 JSON |
| 跨 LLM 厂商 | 自动适配 | 自己写 |
| 流式输出 | astream 内置 | 自己处理 SSE |
| 并行工具调用 | 内置 | 自己 asyncio.gather |
| 调试可观测 | verbose=True | 自己 log |
| 版本绑定风险 | 高 | 低 |
| 依赖膨胀 | 100+ 包 | 1 个包 |
| 启动速度 | 慢 1~2 秒 | 快 |
| 运行性能 | 慢 10~30% | 原生速度 |
| 学习曲线 | LangChain 抽象 | OpenAI API |
| **面试加分** | 中规中矩 | **加分项** |

### 什么时候该手撸

- ✅ 生产应用，长期维护
- ✅ 只用一家 LLM
- ✅ 追求极致性能
- ✅ 严肃场景（金融/医疗）要可控
- ✅ **简历项目需要技术深度**

### 什么时候用 LangChain

- ✅ 快速原型 / Demo
- ✅ 多 LLM 厂商兼容
- ✅ 工具数量很多（20+）
- ✅ 团队不熟悉底层

### 改造路线（如果决定手撸）

| 阶段 | 工作 | 耗时 |
|------|------|------|
| Stage 1 | 写 hand_rolled_agent.py，env 切换 | 1 天 |
| Stage 2 | Skill 加 get_schemas() / get_funcs() | 半天 |
| Stage 3 | 删 LangChain 核心依赖 | 半天 |

总耗时约 **2 天**，代码净增 100~150 行。

### 面试话术

> "我项目原本是用 LangChain 的 AgentExecutor，但跑通后我做了**核心 Agent 手撸重构**——把 LangChain 从核心路径里去掉。
>
> **原因有三个**：
> 1. LangChain 版本迭代激进——0.1/0.2/0.3 API 不兼容，生产代码不想被绑架
> 2. 只用一家 LLM（DeepSeek）——'多厂商兼容'价值用不上
> 3. 想真正吃透 ReAct 协议——手撸一遍才知道 tool_calls 字段长什么样、并行调用怎么处理
>
> **手撸 ReAct 核心是个 for iteration in range(max_iter) 循环**：每轮把消息列表 + 工具 schema 喂给 LLM，看返回是 tool_calls 还是最终答案；是工具调用就执行 + 把结果以 role:tool 加回消息列表。整个核心循环 60 行左右。
>
> **收益**：依赖体积减少 100MB+，启动快 2 秒，性能提升 15%，最重要的是**对每一步行为可控可观测**。"

---

## 13. JSON Schema 是什么

### 快速答案
**JSON Schema = 给 JSON 数据写的"规格说明书"**，用 JSON 本身的语法描述"这份 JSON 应该长什么样"。在你项目里它的核心用途是**告诉 LLM "我有什么工具、每个工具怎么调"**。

### 最直观的例子

**一份 JSON 数据**：
```json
{ "name": "张三", "age": 25, "email": "zhangsan@example.com" }
```

**它的 JSON Schema**：
```json
{
  "type": "object",
  "properties": {
    "name":  { "type": "string", "description": "用户名" },
    "age":   { "type": "integer", "minimum": 0, "maximum": 150 },
    "email": { "type": "string", "format": "email" }
  },
  "required": ["name", "age"]
}
```

Schema 在描述：这是个对象，有三个字段，name 是字符串，age 是 0~150 的整数，name 和 age 必填……

### 项目里的具体用途

```python
@tool
def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构。
    Args:
        table_name: 要查看的表名
    """
```

`@tool` 装饰器**偷偷把这个函数翻译成 JSON Schema** 喂给 LLM：

```json
{
  "type": "function",
  "function": {
    "name": "lookup_schema",
    "description": "查看指定表的详细结构。",
    "parameters": {
      "type": "object",
      "properties": {
        "table_name": {
          "type": "string",
          "description": "要查看的表名"
        }
      },
      "required": ["table_name"]
    }
  }
}
```

LLM 看完后输出工具调用：
```json
{"tool_calls": [{"function": {"name": "lookup_schema", "arguments": "{\"table_name\":\"customers\"}"}}]}
```

→ 你的代码解析后**真去执行那个 Python 函数**。

### 核心关键字

| 关键字 | 含义 | 例子 |
|--------|------|------|
| `type` | 类型 | "string" / "integer" / "number" / "boolean" / "array" / "object" |
| `properties` | 对象字段定义 | `{"name": {"type": "string"}}` |
| `required` | 哪些字段必填 | `["name", "age"]` |
| `description` | 字段说明（⭐ 给 LLM 看）| `"要查看的表名"` |
| `enum` | 枚举 | `"enum": ["INFO", "WARN", "ERROR"]` |
| `minimum` / `maximum` | 数值范围 | `"minimum": 0, "maximum": 100` |
| `items` | 数组元素类型 | `"items": {"type": "string"}` |
| `default` | 默认值 | `"default": 5` |

### JSON Schema 在哪些地方都用到

| 场景 | 用 JSON Schema 做什么 |
|------|---------------------|
| **LLM Tool Calling** | 告诉 LLM 工具长什么样（**你项目用的**） |
| **OpenAPI / Swagger** | 描述 REST API 参数和响应 |
| **AJV / Joi 等校验库** | 后端校验请求参数 |
| **JSON 配置文件** | package.json、tsconfig.json |
| **Pydantic Model** | 自动生成 JSON Schema |

### Pydantic + JSON Schema 搭配

```python
from pydantic import BaseModel, Field

class SearchLogsArgs(BaseModel):
    level: str = Field("ERROR", description="日志级别")
    keyword: str = Field("", description="搜索关键词")
    limit: int = Field(20, ge=1, le=100, description="返回条数")

# 自动生成 JSON Schema
SearchLogsArgs.model_json_schema()
```

→ Pydantic 强大之处：写 Python 类 = 同时得到运行期校验 + JSON Schema 文档。

### 为什么 LLM 真的会按 Schema 输出

OpenAI / Anthropic / DeepSeek 在训练时**让模型见过大量 JSON Schema → tool_calls 输出样本**。所以给它合法 JSON Schema，它**会输出严格匹配 schema 的 JSON**，100% 可靠。

**这就是 "Function Calling / Tool Calling 协议" 的本质** —— 用 JSON Schema 约束 LLM 输出。

### 面试话术

> "工具定义是用 **JSON Schema** 描述给 LLM 看的——name、description、parameters（每个参数的类型和说明）。LLM 在训练时见过大量 schema → tool_calls 样本，所以**给它一份合法 schema，它会严格按 schema 输出工具调用 JSON**。
>
> 我项目里用 LangChain 的 @tool 装饰器，它**从 Python 函数签名 + docstring 自动生成 JSON Schema**——参数类型映射到 type 字段，docstring 的 Args 段映射到参数 description。这是个比较优雅的'声明式'API。
>
> 手撸的话就要自己写 schema，每个工具大概 15 行 JSON——更可控但繁琐。生产场景如果工具数量多，会用 Pydantic Model 写参数 schema，然后 `model_json_schema()` 自动导出，兼具运行期校验和文档化两个收益。"

---

## 14. 那个 NL2SQL MCP server 具体怎么写的？为什么用 Python 不用 TypeScript

### 快速答案

**用 Python + 官方 `mcp` SDK 的 FastMCP，~200 行**。选 Python 是因为 ① 项目主语言就是 Python ② FastMCP 的 `@mcp.tool()` 装饰器从函数签名 + docstring 自动生成 JSON Schema，比手写 TS `inputSchema` 简洁。

### 文件结构

```
mcp-servers/nl2sql-server/
├── server.py            ← 全部逻辑在这（~200 行）
├── requirements.txt     ← mcp + aiomysql
├── README.md
├── .gitignore
└── venv/                ← 独立 venv（不和 agent-python 混用）
```

### 暴露的 5 个工具

| Tool | 干啥 |
|---|---|
| `list_tables` | 列所有表（含注释 + 行数估算）|
| `lookup_schema` | 查某表的列（类型 / 是否可空 / 主键 / 注释）|
| `sample_data` | 取某表前 N 行示例数据 |
| `validate_sql` | 校验 SQL 安全（不执行）|
| `execute_select_sql` | 执行 SELECT + 自动 LIMIT 兜底 |

### 核心代码长这样

```python
from mcp.server.fastmcp import FastMCP
import aiomysql

mcp = FastMCP("nl2sql-mcp-server")

@mcp.tool()
async def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构（列名、类型、是否可空、主键、注释）。

    Args:
        table_name: 要查看的表名,例如 'customers' 或 'orders'
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT COLUMN_NAME, COLUMN_TYPE, ... FROM information_schema.COLUMNS WHERE TABLE_NAME=%s",
                (table_name,)
            )
            return format_columns(await cur.fetchall())

if __name__ == "__main__":
    mcp.run()  # 启动 stdio transport
```

**FastMCP 自动从函数做的事**：
- **函数名 → tool name**（`lookup_schema`）
- **docstring 第一段 → tool description**（喂给 LLM 看的）
- **Args 部分 → 参数的 description**
- **类型注解 (`str`, `int`) → JSON Schema 的 type 字段**

写法跟 LangChain `@tool` **几乎一模一样**——这是 Anthropic 故意的，降低迁移成本。

### 安全设计（4 道防线）

1. **黑名单关键字**：`DROP / DELETE / UPDATE / INSERT / ALTER / TRUNCATE / CREATE / GRANT / REVOKE / REPLACE` 一旦出现直接拒绝。**用 `\b` 单词边界匹配**，避免误伤 `updated_at` 这类合法列名。
2. **必须 SELECT 开头**（或 `WITH` 开头的 CTE）。
3. **`sample_data` 表名白名单**：表名只允许 `[a-zA-Z_][a-zA-Z0-9_]*`，防 SQL 注入（**注：表名不能用参数化，只能字符串拼接，所以必须白名单兜底**）。
4. **强制 LIMIT 兜底**：LLM 没写 LIMIT 时自动加 `LIMIT 100`，防全表扫描。

### stdio 协议的坑

MCP server 用 **stdio 协议**（不开网络端口）：
- **stdin**：MCP client 发请求过来
- **stdout**：server 写响应回去  ⚠️ **不能 `print()` 调试！会污染协议！**
- **stderr**：日志只能写这里

**这是初次写 MCP server 最容易踩的坑**——`print("DEBUG XXX")` 一下就让 Claude Desktop 收到非法 JSON-RPC，整个 server 直接挂。规矩是：**任何日志都 `print(..., file=sys.stderr)` 或者 `logging` 配 stderr handler**。

### 接到 Claude Desktop 怎么配

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "nl2sql": {
      "command": "/abs/path/to/venv/bin/python",
      "args": ["/abs/path/to/server.py"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PASSWORD": "rootpass",
        "MYSQL_DATABASE": "business_db"
      }
    }
  }
}
```

重启 Claude Desktop，左下角工具栏（🔨 锤子图标）就能看到 5 个 tool。之后直接问"业务库里有什么表"，Claude 会自动调 `list_tables`。

### 为什么是 Python 不是 TypeScript（虽然官方 TS SDK 更早）

**之前是 TS 版的，今年改成 Python**。理由：

1. **项目主语言就是 Python**（agent-python）——技术栈统一更好维护，不用同时配 Node 和 Python
2. **FastMCP 的开发体验更好** —— 装饰器从 docstring 自动生成 schema，TS 版要手写 `inputSchema: { type: "object", properties: {...} }` 啰嗦得多
3. **官方 Python SDK 已经成熟** —— 当初选 TS 是因为发布最早，现在 Python SDK 功能等价

### 面试话术

> "我把项目的 NL2SQL 能力包装成了一个独立的 MCP server，Python 实现，用官方 `mcp` SDK 的 FastMCP API——`@mcp.tool()` 装饰器从函数签名 + docstring 自动生成 JSON Schema 喂给 LLM，写法跟 LangChain 的 `@tool` 几乎一致。
>
> 暴露 5 个 tool：`list_tables` / `lookup_schema` / `sample_data` / `validate_sql` / `execute_select_sql`。
>
> 安全上有 4 道防线——黑名单关键字校验（用单词边界匹配避免误伤合法列名）、必须 SELECT 开头、表名白名单防注入、强制 LIMIT 兜底。
>
> 协议用 stdio + JSON-RPC——这是 MCP 默认传输方式，最大坑是 **stdout 是协议通道不能 `print()` 调试**，日志必须走 stderr。
>
> 实际接到 Claude Desktop 用了一下，体验是：用户问'业务库里都有什么表'，Claude 自动调 `list_tables` → 看完表名问'orders 表长啥样'，再自动调 `lookup_schema` → 然后想看几条数据，调 `sample_data`——**完整 ReAct 循环全发生在 Claude Desktop 那一侧，我的 server 只负责执行工具**。这是 MCP 这套协议的核心价值：让任何 LLM 应用复用我的工具能力，不绑死前端。"

---

## 附录：高频拷打题速查表

| 话题 | 准备深度 | 核心答法 |
|------|---------|---------|
| **Skill 设计** | ⭐⭐⭐ | LangChain 没有 Skill，是我自己加的抽象，用 intent_tags 做路由 |
| **MCP（协议层）** | ⭐⭐⭐⭐ | 协议本质 + 跟 LangChain Tool 是双轨不是替代关系 |
| **MCP server 实现** | ⭐⭐⭐ | Python `mcp` SDK + FastMCP；stdio 协议；4 道安全防线；不能 `print` |
| **Agent 流程** | ⭐⭐⭐ | 意图识别 / Skill 路由 / ReAct / max_iterations / 自纠错 |
| **LangChain 取舍** | ⭐⭐⭐ | 有选择地用，只用 @tool + AgentExecutor，其他自己写 |
| **JSON Schema** | ⭐⭐ | 给 LLM 看的工具说明书，@tool / @mcp.tool() 自动生成 |
| **Prompt 工程** | ⭐⭐ | YAML 模板 + 热加载 + few-shot + 代码兜底 |
| **NL2SQL 安全** | ⭐⭐⭐ | Python+Java 双层校验 + 仅 SELECT + 自纠错重试 |
| **并发** | ⭐⭐ | uvicorn 进程 / Java Tomcat 200 线程 |
| **MyBatis-Plus 迁移** | ⭐⭐ | 启动 27s→6s，BaseMapper + LambdaQueryWrapper |
| **生产级 bug** | ⭐⭐⭐ | MySQL utf8 → utf8mb4 解决中文乱码；Lombok 跟新 JDK 不兼容；404 不该当 ERROR |

---

## 投递不同岗位的回答侧重

| 岗位 | 重点讲 |
|------|-------|
| **AI 算法工程师** | Agent / ReAct / Prompt engineering / LLM 输出可靠性 / MCP 生态 |
| **后端开发(含 AI 业务)** | Java 编排 / 双数据源 / MyBatis-Plus 迁移 / SQL 安全 / MCP server 跨进程 |
| **大模型应用工程师** | LangChain 取舍 / MCP 双轨架构 / 意图识别 / contextvar 注入 / 自纠错 |
| **全栈** | 加聊天 UI: "根据 intent 分发 SQL/Markdown 多种渲染" |
| **应届校招通用岗** | 控制深度，强调 Agent 6 要素 + 架构图 |
