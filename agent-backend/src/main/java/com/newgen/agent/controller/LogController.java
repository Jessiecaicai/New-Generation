package com.newgen.agent.controller;

import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.service.LogMonitorService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/logs")
public class LogController {

    @Autowired
    private LogMonitorService logService;

    @GetMapping
    public Page<SystemLog> getLogs(
            @RequestParam(required = false) String level,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return logService.getLogs(level, page, size);
    }

    @GetMapping("/stats")
    public Map<String, Object> getStats(@RequestParam(defaultValue = "24") int hours) {
        return logService.getStats(hours);
    }

    @GetMapping("/{id}/context")
    public Map<String, Object> getContext(@PathVariable Long id) {
        return logService.getLogContext(id);
    }

    @PutMapping("/{id}/resolve")
    public void resolve(@PathVariable Long id) {
        logService.resolveLog(id);
    }

    @PostMapping
    public SystemLog createLog(@RequestBody SystemLog log) {
        return logService.saveLog(log);
    }
}
