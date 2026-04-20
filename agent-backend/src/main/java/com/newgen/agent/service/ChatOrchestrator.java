package com.newgen.agent.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.newgen.agent.model.dto.*;
import com.newgen.agent.model.entity.ChatHistory;
import com.newgen.agent.model.entity.Session;
import com.newgen.agent.repository.ChatHistoryRepository;
import com.newgen.agent.repository.SessionRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

@Slf4j
@Service
public class ChatOrchestrator {

    @Autowired private AgentClientService agentClient;
    @Autowired private SchemaService schemaService;
    @Autowired private SqlExecutionService sqlExecutionService;
    @Autowired private SessionRepository sessionRepo;
    @Autowired private ChatHistoryRepository chatHistoryRepo;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final int MAX_SQL_RETRIES = 3;

    public ChatResponseDto processChat(ChatRequestDto request) {
        // 1. Ensure session
        String sessionId = ensureSession(request.getSessionId());

        // 2. Get schema for NL2SQL
        SchemaMetadataDto schema = schemaService.getFullSchema();
        Map<String, Object> schemaMap = objectMapper.convertValue(schema, Map.class);

        // 3. Build agent request
        AgentRequestDto agentReq = AgentRequestDto.builder()
                .question(request.getQuestion())
                .schema(schemaMap)
                .conversationHistory(request.getConversationHistory())
                .knowledgeBases(request.getKnowledgeBases())
                .intentHint(request.getIntentHint())
                .build();

        // 4. Call Python agent
        AgentResponseDto agentResp = agentClient.sendChatRequest(agentReq);

        // 5. If SQL returned, validate and execute (with retry)
        Object queryResults = null;
        String finalSql = agentResp.getSql();

        if (finalSql != null && !finalSql.isBlank()) {
            queryResults = executeWithRetry(request.getQuestion(), agentReq, finalSql);
            // Update finalSql if retry produced a new one
            if (queryResults instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> resultMap = (Map<String, Object>) queryResults;
                if (resultMap.containsKey("finalSql")) {
                    finalSql = (String) resultMap.remove("finalSql");
                }
            }
        }

        // 6. Save to history
        saveHistory(sessionId, request.getQuestion(), agentResp.getAnswer(),
                agentResp.getIntent(), finalSql);

        // 7. Build response
        return ChatResponseDto.builder()
                .answer(agentResp.getAnswer())
                .intent(agentResp.getIntent())
                .sql(finalSql)
                .queryResults(queryResults)
                .ragSources(agentResp.getRagSources())
                .confidence(agentResp.getConfidence())
                .build();
    }

    private Object executeWithRetry(String question, AgentRequestDto originalReq, String sql) {
        for (int attempt = 0; attempt < MAX_SQL_RETRIES; attempt++) {
            try {
                Map<String, Object> result = sqlExecutionService.executeSql(sql);
                if (!result.containsKey("error")) {
                    result.put("finalSql", sql);
                    return result;
                }

                String error = (String) result.get("error");
                log.warn("SQL execution failed (attempt {}): {}", attempt + 1, error);

                if (attempt < MAX_SQL_RETRIES - 1) {
                    // Retry: call agent with error context
                    Map<String, String> errorCtx = new HashMap<>();
                    errorCtx.put("previousSql", sql);
                    errorCtx.put("errorMessage", error);
                    originalReq.setErrorContext(errorCtx);
                    originalReq.setIntentHint("nl2sql");

                    AgentResponseDto retry = agentClient.sendChatRequest(originalReq);
                    if (retry.getSql() != null) {
                        sql = retry.getSql();
                    } else {
                        return result; // Agent couldn't fix it
                    }
                } else {
                    return result;
                }
            } catch (Exception e) {
                log.error("SQL execution error: {}", e.getMessage());
                if (attempt == MAX_SQL_RETRIES - 1) {
                    Map<String, Object> errorResult = new HashMap<>();
                    errorResult.put("error", e.getMessage());
                    return errorResult;
                }
            }
        }
        return null;
    }

    private String ensureSession(String sessionId) {
        if (sessionId != null && sessionRepo.existsById(sessionId)) {
            return sessionId;
        }
        Session session = new Session();
        session.setId(UUID.randomUUID().toString());
        sessionRepo.save(session);
        return session.getId();
    }

    private void saveHistory(String sessionId, String question, String answer,
                             String intent, String sql) {
        try {
            // Save user message
            ChatHistory userMsg = new ChatHistory();
            userMsg.setId(UUID.randomUUID().toString());
            userMsg.setSessionId(sessionId);
            userMsg.setRole(ChatHistory.Role.USER);
            userMsg.setContent(question);
            userMsg.setIntent(intent);
            chatHistoryRepo.save(userMsg);

            // Save assistant message
            ChatHistory assistantMsg = new ChatHistory();
            assistantMsg.setId(UUID.randomUUID().toString());
            assistantMsg.setSessionId(sessionId);
            assistantMsg.setRole(ChatHistory.Role.ASSISTANT);
            assistantMsg.setContent(answer);
            assistantMsg.setIntent(intent);
            if (sql != null) {
                assistantMsg.setMetadata("{\"sql\":\"" + sql.replace("\"", "\\\"") + "\"}");
            }
            chatHistoryRepo.save(assistantMsg);
        } catch (Exception e) {
            log.error("Failed to save chat history: {}", e.getMessage());
        }
    }
}
