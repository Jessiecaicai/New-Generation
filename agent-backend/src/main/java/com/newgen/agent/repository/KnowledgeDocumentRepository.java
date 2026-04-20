package com.newgen.agent.repository;

import com.newgen.agent.model.entity.KnowledgeDocument;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface KnowledgeDocumentRepository extends JpaRepository<KnowledgeDocument, String> {
    List<KnowledgeDocument> findByKnowledgeBaseId(String knowledgeBaseId);
}
