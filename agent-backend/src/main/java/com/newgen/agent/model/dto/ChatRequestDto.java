package com.newgen.agent.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ChatRequestDto {

    @NotBlank(message = "问题不能为空")
    private String question;

    private String sessionId;
    private List<Map<String, String>> conversationHistory;
    private String intentHint;
}
