package com.newgen.agent.repository;

import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.model.enums.LogLevel;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface SystemLogRepository extends JpaRepository<SystemLog, Long> {

    Page<SystemLog> findByLogLevelOrderByCreatedAtDesc(LogLevel level, Pageable pageable);

    Page<SystemLog> findByIsResolvedFalseAndLogLevelInOrderByCreatedAtDesc(
            List<LogLevel> levels, Pageable pageable);

    long countByLogLevelAndCreatedAtAfter(LogLevel level, LocalDateTime after);

    long countByIsResolvedFalse();

    @Query("SELECT s FROM SystemLog s WHERE s.id BETWEEN :start AND :end ORDER BY s.id")
    List<SystemLog> findContext(@Param("start") Long start, @Param("end") Long end);

    @Query("SELECT s.category, COUNT(s) FROM SystemLog s WHERE s.logLevel = :level AND s.createdAt > :after GROUP BY s.category")
    List<Object[]> countByCategoryAndLevel(@Param("level") LogLevel level, @Param("after") LocalDateTime after);
}
