package com.newgen.agent.model.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;

@Data
public class AgentResponseDto {
    private String answer;
    private String intent;
    private String sql;

    @JsonAlias({"display_sql"})
    private String displaySql;

    private List<Object> toolCalls;
    private Double confidence;
}
