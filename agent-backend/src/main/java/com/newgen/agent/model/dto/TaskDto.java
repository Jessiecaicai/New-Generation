package com.newgen.agent.model.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class TaskDto {
    private String taskId;
    private String status;
    private Integer queuePosition;
    private ChatResponseDto result;
    private String error;
}
