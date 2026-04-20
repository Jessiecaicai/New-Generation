package com.newgen.agent.model.dto;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class AgentResponseDto {
    private String answer;
    private String intent;
    private String sql;
    private List<Map<String, Object>> ragSources;
    private List<Object> toolCalls;
    private Double confidence;
}
