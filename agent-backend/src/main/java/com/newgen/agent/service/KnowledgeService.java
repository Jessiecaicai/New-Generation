package com.newgen.agent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.newgen.agent.config.PathConfig;
import com.newgen.agent.model.entity.KnowledgeBase;
import com.newgen.agent.model.entity.KnowledgeDocument;
import com.newgen.agent.repository.KnowledgeBaseRepository;
import com.newgen.agent.repository.KnowledgeDocumentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Slf4j
@Service
public class KnowledgeService {

    @Autowired private KnowledgeBaseRepository kbRepo;
    @Autowired private KnowledgeDocumentRepository docRepo;
    @Autowired private PathConfig pathConfig;
    @Autowired private RestTemplate restTemplate;

    @Value("${agent.service.url:http://localhost:8001}")
    private String agentServiceUrl;

    public KnowledgeBase createKnowledgeBase(String name, String description) {
        KnowledgeBase kb = new KnowledgeBase();
        kb.setId(UUID.randomUUID().toString());
        kb.setName(name);
        kb.setDescription(description);
        kbRepo.insert(kb);
        return kb;
    }

    public Map<String, Object> uploadDocument(String kbId, MultipartFile file) throws IOException {
        KnowledgeBase kb = kbRepo.selectById(kbId);
        if (kb == null) {
            throw new RuntimeException("知识库不存在: " + kbId);
        }

        // Save file
        Path uploadDir = Paths.get(pathConfig.getKnowledgeUploadDir(), kbId);
        Files.createDirectories(uploadDir);
        Path filePath = uploadDir.resolve(file.getOriginalFilename());
        file.transferTo(filePath.toFile());

        // Save document record
        KnowledgeDocument doc = new KnowledgeDocument();
        doc.setId(UUID.randomUUID().toString());
        doc.setKnowledgeBaseId(kbId);
        doc.setFileName(file.getOriginalFilename());
        doc.setFilePath(filePath.toString());
        doc.setFileSize(file.getSize());
        doc.setFileType(getFileExtension(file.getOriginalFilename()));
        docRepo.insert(doc);

        // Call Python to index
        try {
            Map<String, Object> indexReq = new HashMap<>();
            indexReq.put("knowledge_base_name", kb.getName());
            indexReq.put("file_paths", filePath.toString());

            @SuppressWarnings("unchecked")
            Map<String, Object> result = restTemplate.postForObject(
                    agentServiceUrl + "/knowledge/index", indexReq, Map.class);

            // Update counts
            if (result != null && result.containsKey("total_chunks")) {
                int chunks = (int) result.get("total_chunks");
                doc.setChunkCount(chunks);
                doc.setStatus("INDEXED");
                docRepo.updateById(doc);

                kb.setDocumentCount(kb.getDocumentCount() + 1);
                kb.setChunkCount(kb.getChunkCount() + chunks);
                kbRepo.updateById(kb);
            }
            return result != null ? result : Map.of("status", "indexed");

        } catch (Exception e) {
            doc.setStatus("ERROR");
            doc.setErrorMessage(e.getMessage());
            docRepo.updateById(doc);
            throw new RuntimeException("索引失败: " + e.getMessage());
        }
    }

    public void deleteKnowledgeBase(String id) {
        KnowledgeBase kb = kbRepo.selectById(id);
        if (kb == null) {
            throw new RuntimeException("知识库不存在: " + id);
        }
        try {
            restTemplate.delete(agentServiceUrl + "/knowledge/" + kb.getName());
        } catch (Exception e) {
            log.warn("Failed to delete vector index: {}", e.getMessage());
        }
        docRepo.delete(new LambdaQueryWrapper<KnowledgeDocument>()
                .eq(KnowledgeDocument::getKnowledgeBaseId, id));
        kbRepo.deleteById(id);
    }

    public List<KnowledgeBase> listKnowledgeBases() {
        return kbRepo.selectList(null);
    }

    private String getFileExtension(String filename) {
        if (filename == null) return "";
        int dot = filename.lastIndexOf('.');
        return dot >= 0 ? filename.substring(dot) : "";
    }
}
