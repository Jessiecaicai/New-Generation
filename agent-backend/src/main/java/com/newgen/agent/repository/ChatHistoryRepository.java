package com.newgen.agent.repository;

import com.newgen.agent.model.entity.ChatHistory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatHistoryRepository extends JpaRepository<ChatHistory, String> {
    List<ChatHistory> findBySessionIdOrderByCreatedAtDesc(String sessionId);
}
