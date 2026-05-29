package com.newgen.agent.controller;

import com.newgen.agent.model.dto.ChatRequestDto;
import com.newgen.agent.model.dto.ChatResponseDto;
import com.newgen.agent.service.ChatOrchestrator;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

/**
 * 对话入口 —— 同步处理，直接返回结果。
 * 简化版（去掉了任务队列 + 轮询机制）。
 */
@RestController
@RequestMapping("/api")
public class ChatController {

    @Autowired
    private ChatOrchestrator orchestrator;

    @PostMapping("/chat")
    public ChatResponseDto chat(@Valid @RequestBody ChatRequestDto request) {
        return orchestrator.processChat(request);
    }
}
