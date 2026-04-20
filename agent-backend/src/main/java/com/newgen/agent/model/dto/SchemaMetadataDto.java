package com.newgen.agent.model.dto;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class SchemaMetadataDto {
    private List<TableInfo> tables;

    @Data
    public static class TableInfo {
        private String name;
        private String comment;
        private List<ColumnInfo> columns;
        private List<Map<String, Object>> sampleData;
    }

    @Data
    public static class ColumnInfo {
        private String name;
        private String type;
        private boolean nullable;
        private String comment;
    }
}
