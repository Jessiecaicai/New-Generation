package com.newgen.agent.model.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@Builder
public class ChatResponseDto {
    private String answer;
    private String intent;
    private String sql;
    private Object queryResults;  // {columns, rows, rowCount}
    private List<Map<String, Object>> ragSources;
    private Double confidence;
}
