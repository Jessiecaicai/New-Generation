package com.newgen.agent.model.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@Builder
public class AgentRequestDto {
    private String question;
    private Map<String, Object> schema;
    private List<Map<String, String>> conversationHistory;
    private List<String> knowledgeBases;
    private Map<String, String> errorContext;
    private String intentHint;
}
