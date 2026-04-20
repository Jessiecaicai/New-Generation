package com.newgen.agent.controller;

import com.newgen.agent.model.dto.ChatRequestDto;
import com.newgen.agent.model.dto.TaskDto;
import com.newgen.agent.service.TaskManager;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class ChatController {

    @Autowired
    private TaskManager taskManager;

    @PostMapping("/chat")
    public TaskDto submitChat(@Valid @RequestBody ChatRequestDto request) {
        return taskManager.submitTask(request);
    }

    @GetMapping("/tasks/{taskId}")
    public TaskDto getTask(@PathVariable String taskId) {
        return taskManager.getTask(taskId);
    }
}
