package com.newgen.agent.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.service.LogMonitorService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/logs")
public class LogController {

    @Autowired
    private LogMonitorService logService;

    @GetMapping
    public Map<String, Object> getLogs(
            @RequestParam(required = false) String level,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        IPage<SystemLog> mpPage = logService.getLogs(level, page, size);
        // 适配前端（前端读 content / totalElements / totalPages）
        Map<String, Object> body = new HashMap<>();
        body.put("content", mpPage.getRecords());
        body.put("totalElements", mpPage.getTotal());
        body.put("totalPages", mpPage.getPages());
        body.put("size", mpPage.getSize());
        body.put("number", page);
        body.put("numberOfElements", mpPage.getRecords().size());
        return body;
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
