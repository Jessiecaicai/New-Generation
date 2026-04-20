package com.newgen.agent.service;

import com.newgen.agent.exception.SqlValidationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;

@Slf4j
@Service
public class SqlExecutionService {

    @Autowired
    @org.springframework.beans.factory.annotation.Qualifier("businessJdbcTemplate")
    private JdbcTemplate jdbcTemplate;

    private static final Set<String> DANGEROUS_KEYWORDS = Set.of(
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
            "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    );

    public String validateSql(String sql) {
        if (sql == null || sql.isBlank()) {
            throw new SqlValidationException("SQL 不能为空");
        }

        String upper = sql.trim().toUpperCase();

        // Must start with SELECT (or WITH for CTEs)
        if (!upper.startsWith("SELECT") && !upper.startsWith("WITH")) {
            throw new SqlValidationException("只允许 SELECT 查询");
        }

        // Check dangerous keywords
        for (String kw : DANGEROUS_KEYWORDS) {
            // Check as whole word
            if (upper.matches(".*\\b" + kw + "\\b.*")) {
                throw new SqlValidationException("检测到危险关键字: " + kw);
            }
        }

        // Add LIMIT if missing
        if (!upper.contains("LIMIT")) {
            sql = sql.trim();
            if (sql.endsWith(";")) {
                sql = sql.substring(0, sql.length() - 1);
            }
            sql += " LIMIT 100";
            log.info("Auto-added LIMIT 100");
        }

        return sql;
    }

    public Map<String, Object> executeSql(String sql) {
        sql = validateSql(sql);
        log.info("Executing SQL: {}", sql);

        try {
            // Set query timeout
            jdbcTemplate.setQueryTimeout(30);
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql);

            // Extract column names from first row
            List<String> columns = new ArrayList<>();
            if (!rows.isEmpty()) {
                columns.addAll(rows.get(0).keySet());
            }

            Map<String, Object> result = new HashMap<>();
            result.put("columns", columns);
            result.put("rows", rows);
            result.put("rowCount", rows.size());
            return result;

        } catch (Exception e) {
            log.error("SQL execution failed: {}", e.getMessage());
            Map<String, Object> result = new HashMap<>();
            result.put("error", e.getMessage());
            result.put("sql", sql);
            return result;
        }
    }
}
