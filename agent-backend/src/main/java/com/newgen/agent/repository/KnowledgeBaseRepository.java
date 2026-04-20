package com.newgen.agent.repository;

import com.newgen.agent.model.entity.KnowledgeBase;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface KnowledgeBaseRepository extends JpaRepository<KnowledgeBase, String> {
    Optional<KnowledgeBase> findByName(String name);
}
