# NL2SQL MCP Server (Python)

把项目的 NL2SQL 能力包装成符合 **Model Context Protocol** 的独立服务，让 Claude Desktop / Cursor / Cline 等 MCP client 能直接调用，**不必经过项目的前端或 Java 后端**。

## 暴露的 5 个工具

| Tool | 干嘛 |
|---|---|
| `list_tables` | 列出业务数据库 `business_db` 所有表 |
| `lookup_schema` | 查指定表的字段结构（类型 / 是否可空 / 主键 / 注释） |
| `sample_data` | 看指定表的前 N 行数据 |
| `validate_sql` | 校验 SQL 安全性（不执行）|
| `execute_select_sql` | 真执行 SELECT 并返回结果（最终拿数据用）|

## 安全设计（很重要）

1. **只允许 SELECT** —— 黑名单关键字（DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE/CREATE/GRANT/REVOKE/REPLACE），用 `\b` 单词边界匹配，**不会误伤 `updated_at` 这类列名**
2. **强制 LIMIT 兜底** —— LLM 没写 LIMIT 时自动加 `LIMIT 100`，防全表扫描
3. **表名白名单** —— `sample_data` 工具里表名只允许 `[a-zA-Z_][a-zA-Z0-9_]*`，防 SQL 注入
4. **建议用只读 MySQL 账号** —— 本地图省事用 root，生产环境务必单独建个只授 SELECT 权限的账号

## 本地启动 & 调试

```bash
# 1. 建独立 venv
python3.11 -m venv venv
source venv/bin/activate

# 2. 装依赖
pip install -r requirements.txt

# 3. 配数据库（用环境变量或 export）
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=rootpass
export MYSQL_DATABASE=business_db

# 4. 起 server（会阻塞，等 MCP client 连过来）
python server.py
```

⚠️ 起来后会**卡住等 stdin**，这是对的。MCP server 是 stdio 协议——client 通过 stdin 发请求 / stdout 收响应。手动跑只是验证能起，要真用得有 client 连。

## 接到 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "nl2sql": {
      "command": "/Users/jessie/C/CodeRepository/Working/New-Generation/mcp-servers/nl2sql-server/venv/bin/python",
      "args": [
        "/Users/jessie/C/CodeRepository/Working/New-Generation/mcp-servers/nl2sql-server/server.py"
      ],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "rootpass",
        "MYSQL_DATABASE": "business_db"
      }
    }
  }
}
```

重启 Claude Desktop，左下角工具栏（🔧 / 锤子图标）应该能看到 `nl2sql-mcp-server`，里面 5 个 tool。然后直接问："业务库里都有什么表？" → Claude 会自动调 `list_tables`。

## 接到 Cursor

Cursor 也支持 MCP，配置位置：`~/.cursor/mcp.json`，格式相同。

## 协议细节

- **传输**：stdio（不开 HTTP 端口）
- **格式**：JSON-RPC 2.0
- **stdin**：client → server 的请求
- **stdout**：server → client 的响应 **（⚠️ 千万不能用 `print()`，会污染协议！）**
- **stderr**：服务器自己的日志（client 不读 stderr，可以随便打）

## 为什么是 Python（而不是 TypeScript）

- 项目主语言是 Python（`agent-python/`），技术栈统一更好维护
- Python MCP SDK (`mcp` package) 官方维护，功能跟 TS SDK 等价
- FastMCP 的 `@mcp.tool()` 装饰器从 docstring + 类型注解自动生成 JSON Schema，**比 TS 版的手写 inputSchema 更简洁**

## 跟 agent-python 里 NL2SQL Skill 的关系

| | agent-python 里的 NL2SQL Skill | 这个 MCP server |
|---|---|---|
| 消费方 | 项目自家前端 → Java backend → Python agent | 任何 MCP client（Claude Desktop / Cursor）|
| 调用方式 | 进程内函数（LangChain `@tool`）| 跨进程 JSON-RPC over stdio |
| 性能 | 纳秒级 | 毫秒级（多一次序列化）|
| 对外开放 | 不对外 | 对外可用（生态接入）|

**两者是设计上的"双轨"**：内部高性能、对外标准协议。
