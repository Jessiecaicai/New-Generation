package com.newgen.agent.service;

import com.newgen.agent.model.dto.SchemaMetadataDto;
import com.newgen.agent.model.dto.SchemaMetadataDto.ColumnInfo;
import com.newgen.agent.model.dto.SchemaMetadataDto.TableInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
public class SchemaService {

    @Autowired
    @org.springframework.beans.factory.annotation.Qualifier("businessJdbcTemplate")
    private JdbcTemplate jdbcTemplate;

    private final Map<String, SchemaMetadataDto> cache = new ConcurrentHashMap<>();
    private long cacheTimestamp = 0;
    private static final long CACHE_TTL = 5 * 60 * 1000; // 5 minutes

    public SchemaMetadataDto getFullSchema() {
        if (System.currentTimeMillis() - cacheTimestamp < CACHE_TTL && cache.containsKey("schema")) {
            return cache.get("schema");
        }

        SchemaMetadataDto schema = new SchemaMetadataDto();
        List<TableInfo> tables = new ArrayList<>();

        String dbName = getCurrentDatabase();
        List<Map<String, Object>> tableRows = jdbcTemplate.queryForList(
                "SELECT TABLE_NAME, TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES " +
                "WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'", dbName);

        for (Map<String, Object> row : tableRows) {
            String tableName = (String) row.get("TABLE_NAME");
            TableInfo table = new TableInfo();
            table.setName(tableName);
            table.setComment((String) row.get("TABLE_COMMENT"));
            table.setColumns(getColumns(dbName, tableName));
            table.setSampleData(getSampleData(tableName));
            tables.add(table);
        }

        schema.setTables(tables);
        cache.put("schema", schema);
        cacheTimestamp = System.currentTimeMillis();
        log.info("Schema refreshed: {} tables", tables.size());
        return schema;
    }

    private List<ColumnInfo> getColumns(String dbName, String tableName) {
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT " +
                "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? " +
                "ORDER BY ORDINAL_POSITION", dbName, tableName);
        List<ColumnInfo> cols = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            ColumnInfo col = new ColumnInfo();
            col.setName((String) row.get("COLUMN_NAME"));
            col.setType((String) row.get("COLUMN_TYPE"));
            col.setNullable("YES".equals(row.get("IS_NULLABLE")));
            col.setComment((String) row.get("COLUMN_COMMENT"));
            cols.add(col);
        }
        return cols;
    }

    private List<Map<String, Object>> getSampleData(String tableName) {
        try {
            // Safe: tableName comes from INFORMATION_SCHEMA, not user input
            return jdbcTemplate.queryForList("SELECT * FROM `" + tableName + "` LIMIT 3");
        } catch (Exception e) {
            log.warn("Cannot get sample data for {}: {}", tableName, e.getMessage());
            return Collections.emptyList();
        }
    }

    private String getCurrentDatabase() {
        return jdbcTemplate.queryForObject("SELECT DATABASE()", String.class);
    }

    public void invalidateCache() {
        cache.clear();
        cacheTimestamp = 0;
    }
}
