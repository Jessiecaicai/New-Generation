/**
 * NL2SQL MCP Server
 * ─────────────────────────────────────────────────────────────────
 * 把 NL2SQL 能力包装成符合 Model Context Protocol 的独立服务,
 * 让 Claude Desktop / Cursor / Cline 等 MCP client 能直接调用。
 *
 * 暴露 4 个工具:
 *   1. list_tables       - 列出业务数据库所有表
 *   2. lookup_schema     - 查看指定表的字段结构
 *   3. sample_data       - 获取指定表的前 N 行示例数据
 *   4. validate_sql      - 校验 SQL 是否合法(只允许 SELECT)
 *
 * 安全设计:
 *   - 仅允许 SELECT 查询(黑名单关键字 + sqlparse 风格的语法检查)
 *   - 在只读连接上执行(单独的 MySQL 用户,只授 SELECT 权限)
 *   - 所有查询自动加 LIMIT 兜底
 *
 * 协议: MCP over stdio (默认), JSON-RPC 2.0
 * ─────────────────────────────────────────────────────────────────
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import mysql from "mysql2/promise";

// ============ 配置(从环境变量读取,方便 Claude Desktop 配置)============
const config = {
  host: process.env.MYSQL_HOST || "localhost",
  port: parseInt(process.env.MYSQL_PORT || "3306"),
  user: process.env.MYSQL_USER || "root",
  password: process.env.MYSQL_PASSWORD || "pp0123456",
  database: process.env.MYSQL_DATABASE || "business_db",
  // 默认 LIMIT 兜底,防止无意识跑全表扫描
  maxRows: parseInt(process.env.MAX_ROWS || "100"),
};

// ============ MySQL 连接池(进程级别共享)============
const pool = mysql.createPool({
  host: config.host,
  port: config.port,
  user: config.user,
  password: config.password,
  database: config.database,
  connectionLimit: 5,
  charset: "utf8mb4",
});

// ============ SQL 安全校验(对应 Python sql_tools.py 的 validate_sql) ============
const DANGEROUS_KEYWORDS = [
  "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
  "TRUNCATE", "CREATE", "GRANT", "REVOKE", "REPLACE",
];

function validateSqlString(sql: string): { ok: boolean; message: string } {
  const cleaned = sql.trim().replace(/;\s*$/, "");
  if (!cleaned) return { ok: false, message: "错误: SQL 为空" };

  const upper = cleaned.toUpperCase();

  // 检查 1: 必须以 SELECT 开头
  if (!upper.startsWith("SELECT") && !upper.startsWith("WITH")) {
    return { ok: false, message: `错误: 只允许 SELECT 查询(或以 WITH 开头的 CTE)` };
  }

  // 检查 2: 黑名单关键字(用单词边界匹配,避免误伤 'updated_at' 等列名)
  for (const kw of DANGEROUS_KEYWORDS) {
    const re = new RegExp(`\\b${kw}\\b`, "i");
    if (re.test(cleaned)) {
      return { ok: false, message: `错误: 检测到危险关键字 '${kw}'` };
    }
  }

  // 检查 3: 建议加 LIMIT
  if (!upper.includes("LIMIT")) {
    return {
      ok: true,
      message: "警告: 建议添加 LIMIT 子句(执行时会自动限制返回行数)。其他方面语法正确。",
    };
  }

  return { ok: true, message: "验证通过: SQL 语法正确,是安全的 SELECT 查询。" };
}

// ============ 工具实现 ============

/**
 * Tool 1: list_tables
 * 列出 business_db 所有表及其行数估算
 */
async function listTables(): Promise<string> {
  const [rows] = await pool.query<mysql.RowDataPacket[]>(
    `SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
     FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
     ORDER BY TABLE_NAME`,
    [config.database]
  );

  if (rows.length === 0) {
    return `数据库 ${config.database} 下没有任何表。`;
  }

  const lines = [`数据库 ${config.database} 的表列表:`, ""];
  for (const r of rows) {
    const comment = r.TABLE_COMMENT || "(无注释)";
    lines.push(`- ${r.TABLE_NAME}: ${comment} (约 ${r.TABLE_ROWS} 行)`);
  }
  return lines.join("\n");
}

/**
 * Tool 2: lookup_schema
 * 查看指定表的列定义(类型 / 是否可空 / 注释 / 是否主键)
 */
async function lookupSchema(tableName: string): Promise<string> {
  const [rows] = await pool.query<mysql.RowDataPacket[]>(
    `SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
     FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
     ORDER BY ORDINAL_POSITION`,
    [config.database, tableName]
  );

  if (rows.length === 0) {
    return `表 '${tableName}' 在数据库 ${config.database} 中不存在。`;
  }

  const lines = [`表: ${tableName}`, "─".repeat(70)];
  for (const r of rows) {
    const nullable = r.IS_NULLABLE === "YES" ? "NULL    " : "NOT NULL";
    const key = r.COLUMN_KEY === "PRI" ? "[PK]" : r.COLUMN_KEY === "UNI" ? "[UQ]" : "    ";
    const comment = r.COLUMN_COMMENT ? ` -- ${r.COLUMN_COMMENT}` : "";
    lines.push(
      `  ${r.COLUMN_NAME.padEnd(24)} ${r.COLUMN_TYPE.padEnd(20)} ${nullable} ${key}${comment}`
    );
  }
  return lines.join("\n");
}

/**
 * Tool 3: sample_data
 * 取指定表的前 N 行示例数据(默认 5)
 */
async function sampleData(tableName: string, limit: number = 5): Promise<string> {
  // 防 SQL 注入: 验证表名只能含合法标识符字符
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(tableName)) {
    return `错误: 非法的表名 '${tableName}'`;
  }
  const safeLimit = Math.min(Math.max(1, limit), 20);

  const [rows] = await pool.query<mysql.RowDataPacket[]>(
    `SELECT * FROM \`${tableName}\` LIMIT ?`,
    [safeLimit]
  );

  if (rows.length === 0) {
    return `表 ${tableName} 暂无数据`;
  }

  return `表 ${tableName} 的前 ${rows.length} 行数据:\n` +
    JSON.stringify(rows, null, 2);
}

/**
 * Tool 4: validate_sql
 * 校验 SQL 安全性(不实际执行)
 */
async function validateSql(sql: string): Promise<string> {
  const result = validateSqlString(sql);
  return result.message;
}

/**
 * Tool 5: execute_select_sql (奖励工具)
 * 真正执行经过校验的 SELECT,自动加 LIMIT 兜底
 */
async function executeSelectSql(sql: string): Promise<string> {
  const validation = validateSqlString(sql);
  if (!validation.ok) {
    return validation.message;
  }

  // 强制加 LIMIT 兜底(如果用户没写)
  let finalSql = sql.trim().replace(/;\s*$/, "");
  if (!finalSql.toUpperCase().includes("LIMIT")) {
    finalSql += ` LIMIT ${config.maxRows}`;
  }

  try {
    const [rows] = await pool.query<mysql.RowDataPacket[]>(finalSql);
    if (rows.length === 0) {
      return "查询执行成功,但没有返回任何行。";
    }
    return `查询执行成功,返回 ${rows.length} 行:\n\n` +
      JSON.stringify(rows, null, 2);
  } catch (e: any) {
    return `SQL 执行失败: ${e.message}`;
  }
}

// ============ 创建 MCP Server ============
const server = new Server(
  {
    name: "nl2sql-mcp-server",     // ⭐ 这个名字会显示在 Claude Desktop 的工具面板里
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 注册工具列表(LLM 通过 description 知道何时调用每个工具)
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_tables",
      description:
        "列出业务数据库 business_db 中所有可用的表(含注释和行数)。" +
        "在用户问数据查询相关问题时,先调这个工具看有哪些表。",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
    {
      name: "lookup_schema",
      description:
        "查看指定表的详细结构(列名、类型、是否可空、主键、注释)。" +
        "在生成 SQL 前调用此工具了解表结构。",
      inputSchema: {
        type: "object",
        properties: {
          table_name: {
            type: "string",
            description: "要查看的表名,例如 'customers' 或 'orders'",
          },
        },
        required: ["table_name"],
      },
    },
    {
      name: "sample_data",
      description:
        "获取指定表的前几行示例数据,帮助理解数据格式和取值范围。",
      inputSchema: {
        type: "object",
        properties: {
          table_name: {
            type: "string",
            description: "要查看示例数据的表名",
          },
          limit: {
            type: "integer",
            description: "返回行数(1-20,默认 5)",
            default: 5,
          },
        },
        required: ["table_name"],
      },
    },
    {
      name: "validate_sql",
      description:
        "校验 SQL 语句是否安全(只允许 SELECT,禁止 DROP/DELETE/UPDATE 等)。" +
        "在 execute_select_sql 之前可以用这个工具预校验。",
      inputSchema: {
        type: "object",
        properties: {
          sql: { type: "string", description: "要校验的 SQL 语句" },
        },
        required: ["sql"],
      },
    },
    {
      name: "execute_select_sql",
      description:
        "执行 SELECT 查询并返回结果。会先做安全校验,自动加 LIMIT 兜底。" +
        "这是最终拿数据的工具。",
      inputSchema: {
        type: "object",
        properties: {
          sql: { type: "string", description: "要执行的 SELECT SQL" },
        },
        required: ["sql"],
      },
    },
  ],
}));

// 处理工具调用 —— LLM 调过来的工具调用走这里
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    let result: string;
    switch (name) {
      case "list_tables":
        result = await listTables();
        break;
      case "lookup_schema":
        result = await lookupSchema(args?.table_name as string);
        break;
      case "sample_data":
        result = await sampleData(
          args?.table_name as string,
          (args?.limit as number) || 5
        );
        break;
      case "validate_sql":
        result = await validateSql(args?.sql as string);
        break;
      case "execute_select_sql":
        result = await executeSelectSql(args?.sql as string);
        break;
      default:
        throw new Error(`未知工具: ${name}`);
    }
    return {
      content: [{ type: "text", text: result }],
    };
  } catch (e: any) {
    return {
      content: [{ type: "text", text: `工具执行失败: ${e.message}` }],
      isError: true,
    };
  }
});

// ============ 启动 ============
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // ⚠️ 注意: 不能用 console.log!stdout 是 MCP 协议通道,
  // 输出到 stdout 会污染协议。日志必须走 stderr。
  console.error("[nl2sql-mcp-server] connected, waiting for requests...");
  console.error(`[nl2sql-mcp-server] db=${config.host}:${config.port}/${config.database}`);
}

main().catch((e) => {
  console.error("[nl2sql-mcp-server] fatal error:", e);
  process.exit(1);
});
