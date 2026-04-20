package com.newgen.agent.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.newgen.agent.model.dto.ChatRequestDto;
import com.newgen.agent.model.dto.ChatResponseDto;
import com.newgen.agent.model.dto.TaskDto;
import com.newgen.agent.model.entity.Session;
import com.newgen.agent.model.entity.Task;
import com.newgen.agent.model.enums.TaskStatus;
import com.newgen.agent.repository.SessionRepository;
import com.newgen.agent.repository.TaskRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
public class TaskManager {

    @Autowired private ChatOrchestrator orchestrator;
    @Autowired private TaskRepository taskRepo;
    @Autowired private SessionRepository sessionRepo;
    @Autowired @Lazy private TaskManager self;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final Map<String, TaskDto> taskCache = new ConcurrentHashMap<>();

    public TaskDto submitTask(ChatRequestDto request) {
        String taskId = UUID.randomUUID().toString();

        // Ensure session exists BEFORE saving Task (FK constraint: tasks.session_id → sessions.id)
        String sessionId = ensureSession(request.getSessionId());
        request.setSessionId(sessionId);

        // Persist task
        Task task = new Task();
        task.setId(taskId);
        task.setSessionId(sessionId);
        task.setQuestion(request.getQuestion());
        task.setStatus(TaskStatus.QUEUED);
        task.setQueuePosition((int) taskRepo.countByStatus(TaskStatus.QUEUED));
        taskRepo.save(task);

        TaskDto dto = TaskDto.builder()
                .taskId(taskId)
                .status("QUEUED")
                .queuePosition(task.getQueuePosition())
                .build();
        taskCache.put(taskId, dto);

        // Execute async (via self proxy so @Async takes effect)
        self.executeAsync(taskId, request);

        return dto;
    }

    @Async("agentTaskExecutor")
    public void executeAsync(String taskId, ChatRequestDto request) {
        log.info("Processing task: {}", taskId);

        // Update status
        updateStatus(taskId, "PROCESSING", null, null);

        try {
            ChatResponseDto result = orchestrator.processChat(request);

            updateStatus(taskId, "SUCCESS", result, null);
            log.info("Task completed: {}", taskId);

        } catch (Exception e) {
            log.error("Task failed: {} - {}", taskId, e.getMessage());
            updateStatus(taskId, "ERROR", null, e.getMessage());
        }
    }

    private String ensureSession(String sessionId) {
        if (sessionId != null && !sessionId.isBlank() && sessionRepo.existsById(sessionId)) {
            return sessionId;
        }
        Session session = new Session();
        session.setId(sessionId != null && !sessionId.isBlank() ? sessionId : UUID.randomUUID().toString());
        sessionRepo.save(session);
        return session.getId();
    }

    public TaskDto getTask(String taskId) {
        TaskDto cached = taskCache.get(taskId);
        if (cached != null) {
            return cached;
        }
        // Fall back to DB
        return taskRepo.findById(taskId).map(t -> TaskDto.builder()
                .taskId(t.getId())
                .status(t.getStatus().name())
                .queuePosition(t.getQueuePosition())
                .error(t.getErrorMessage())
                .build()
        ).orElse(TaskDto.builder().taskId(taskId).status("NOT_FOUND").build());
    }

    private void updateStatus(String taskId, String status, ChatResponseDto result, String error) {
        TaskDto dto = TaskDto.builder()
                .taskId(taskId)
                .status(status)
                .result(result)
                .error(error)
                .build();
        taskCache.put(taskId, dto);

        try {
            taskRepo.findById(taskId).ifPresent(task -> {
                task.setStatus(TaskStatus.valueOf(status));
                task.setErrorMessage(error);
                if ("PROCESSING".equals(status)) {
                    task.setStartedAt(LocalDateTime.now());
                }
                if ("SUCCESS".equals(status) || "ERROR".equals(status)) {
                    task.setCompletedAt(LocalDateTime.now());
                    if (result != null) {
                        try {
                            task.setResult(objectMapper.writeValueAsString(result));
                            task.setIntent(result.getIntent());
                        } catch (Exception e) {
                            log.warn("Failed to serialize result: {}", e.getMessage());
                        }
                    }
                }
                taskRepo.save(task);
            });
        } catch (Exception e) {
            log.error("Failed to update task in DB: {}", e.getMessage());
        }
    }
}
