package com.newgen.agent.controller;

import com.newgen.agent.model.entity.KnowledgeBase;
import com.newgen.agent.service.KnowledgeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @Autowired
    private KnowledgeService knowledgeService;

    @GetMapping
    public List<KnowledgeBase> list() {
        return knowledgeService.listKnowledgeBases();
    }

    @PostMapping
    public KnowledgeBase create(@RequestParam String name,
                                @RequestParam(required = false) String description) {
        return knowledgeService.createKnowledgeBase(name, description);
    }

    @PostMapping("/{id}/documents")
    public Map<String, Object> uploadDocument(@PathVariable String id,
                                              @RequestParam("file") MultipartFile file) throws IOException {
        return knowledgeService.uploadDocument(id, file);
    }

    @DeleteMapping("/{id}")
    public Map<String, String> delete(@PathVariable String id) {
        knowledgeService.deleteKnowledgeBase(id);
        return Map.of("message", "已删除");
    }
}
