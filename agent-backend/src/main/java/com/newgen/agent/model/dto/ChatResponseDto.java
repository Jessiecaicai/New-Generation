package com.newgen.agent.model.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ChatResponseDto {
    private String answer;
    private String intent;
    private String sql;           // 标准 SQL（执行用）
    private String displaySql;    // 直观 SQL（带中文别名，给用户看）
    private Object queryResults;  // {columns, rows, rowCount}
    private Double confidence;
}
