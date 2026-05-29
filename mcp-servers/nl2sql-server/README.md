# NL2SQL MCP Server

> 把 NL2SQL 能力包装成符合 **Model Context Protocol** 的独立服务,让 **Claude Desktop / Cursor / Cline** 等 MCP client 直接调用你的 MySQL 业务数据库。

这是 **Multi-Skill AI Agent 平台**项目的 MCP 化产物 —— 同一份 NL2SQL 工具实现,既能被自家 Agent(通过 LangChain `@tool` 进程内调用),也能通过 MCP 协议被任意 MCP client 跨进程使用。

---

## 🛠️ 提供的工具

| 工具名 | 作用 |
|--------|------|
| `list_tables` | 列出业务数据库所有表(含注释和行数估算) |
| `lookup_schema` | 查看指定表的字段结构(类型 / 可空 / 主键 / 注释) |
| `sample_data` | 获取指定表的前 N 行示例数据 |
| `validate_sql` | 校验 SQL 是否安全(只允许 SELECT) |
| `execute_select_sql` | 执行 SELECT 查询并返回结果(自动加 LIMIT 兜底) |

---

## 🚀 快速开始

### 1. 构建

```bash
cd mcp-servers/nl2sql-server
npm install
npm run build
```

### 2. 接入 Claude Desktop

编辑配置文件:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

添加如下配置:

```json
{
  "mcpServers": {
    "nl2sql": {
      "command": "node",
      "args": [
        "/Users/jessie/com/New-Generation/mcp-servers/nl2sql-server/build/index.js"
      ],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "business_db",
        "MAX_ROWS": "100"
      }
    }
  }
}
```

⚠️ **重要**: `args` 里的路径必须是**绝对路径**,Claude Desktop 不识别相对路径或 `~`。

### 3. 重启 Claude Desktop

完全退出 Claude Desktop(Cmd+Q / 右键托盘退出),重新打开。

### 4. 验证连接成功

在 Claude Desktop 对话框右下角应该出现 🔨 **锤子图标**——点开后能看到:

```
nl2sql (Server)
   ├─ list_tables
   ├─ lookup_schema
   ├─ sample_data
   ├─ validate_sql
   └─ execute_select_sql
```

### 5. 试一下

直接对 Claude 说:

> 查我本地数据库 business_db 里销售额前 5 的客户

Claude 会:
1. 调 `list_tables` 看有哪些表
2. 调 `lookup_schema("customers")` 看字段
3. 写 SQL 并调 `validate_sql` 校验
4. 调 `execute_select_sql` 真的拿数据
5. 综合后给你**真实的查询结果**

---

## 🌟 Cursor 接入

Cursor 用同样的协议。在 Cursor Settings → Features → Model Context Protocol 添加:

```json
{
  "mcpServers": {
    "nl2sql": {
      "command": "node",
      "args": ["/Users/jessie/com/New-Generation/mcp-servers/nl2sql-server/build/index.js"],
      "env": { "MYSQL_PASSWORD": "your_password" }
    }
  }
}
```

---

## 🏗️ 实现细节

### 协议层

- **底层**: JSON-RPC 2.0 over stdio
- **SDK**: `@modelcontextprotocol/sdk` v1.x(官方 TypeScript SDK)
- **能力**: 仅声明 `tools`(不提供 resources / prompts)

### 安全设计

| 层 | 措施 |
|----|------|
| **协议层** | stdio 传输,只有本机能调用,无端口暴露 |
| **SQL 校验** | 必须 SELECT 开头 + 黑名单关键字(DROP/DELETE/UPDATE 等) |
| **关键字检查** | 用 `\\bWORD\\b` 单词边界匹配,避免误伤 `updated_at` 这类列名 |
| **LIMIT 兜底** | 没写 LIMIT 自动加 `LIMIT 100`,防止全表扫描 |
| **表名注入防护** | `sample_data` 接受的 table_name 必须匹配 `^[a-zA-Z_][a-zA-Z0-9_]*$` |
| **连接权限** | 推荐用单独的只读 MySQL 用户(`GRANT SELECT` 即可) |

### stdio 协议注意事项

⚠️ **不能用 `console.log()`**!stdout 是 MCP 协议通道,任何 stdout 输出会破坏 JSON-RPC 消息。所有日志必须走 `console.error()`(stderr)。

---

## 🆚 和项目自家 Agent 的关系

**同一份 NL2SQL 工具实现,两种暴露方式**:

```
                ┌── NL2SQL 工具核心 ──┐
                └─────────┬─────────┘
                          │
              ┌───────────┼────────────┐
              ▼                        ▼
   [agent-python/.../skills/]    [mcp-servers/nl2sql-server/]
   LangChain @tool 装饰          @mcp.tool() 等价(TS 版)
              │                        │
              ▼                        ▼
   ┌──────────────────────┐    ┌────────────────────┐
   │ 自家 AgentEngine     │    │ MCP server 进程    │
   │ (进程内调用)         │    │ (stdio 跨进程)     │
   └──────────────────────┘    └─────────┬──────────┘
              │                          │
              ▼                          ▼
        浏览器前端用户             Claude Desktop / Cursor /
                                  其他 MCP client
```

**为什么这么设计**:

| 场景 | 选哪种 |
|------|-------|
| 自家 Agent 系统内调用 | **LangChain Tool**(纳秒级,无序列化开销) |
| 让 Claude Desktop / Cursor 等外部 Agent 用 | **MCP server**(标准协议,生态兼容) |

→ **协议选择反映消费方差异**,不是技术取代。

---

## 📚 参考

- [Model Context Protocol 规范](https://modelcontextprotocol.io/)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Claude Desktop MCP 文档](https://modelcontextprotocol.io/quickstart/user)
