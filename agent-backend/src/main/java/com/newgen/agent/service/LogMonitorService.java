package com.newgen.agent.service;

import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.model.enums.LogLevel;
import com.newgen.agent.repository.SystemLogRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
public class LogMonitorService {

    @Autowired
    private SystemLogRepository logRepo;

    public SystemLog saveLog(SystemLog logEntry) {
        return logRepo.save(logEntry);
    }

    public Page<SystemLog> getLogs(String level, int page, int size) {
        if (level != null && !level.isBlank()) {
            return logRepo.findByLogLevelOrderByCreatedAtDesc(
                    LogLevel.valueOf(level.toUpperCase()),
                    PageRequest.of(page, size));
        }
        return logRepo.findAll(PageRequest.of(page, size));
    }

    public Map<String, Object> getStats(int hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(hours);
        Map<String, Object> stats = new HashMap<>();
        stats.put("errorCount", logRepo.countByLogLevelAndCreatedAtAfter(LogLevel.ERROR, since));
        stats.put("warnCount", logRepo.countByLogLevelAndCreatedAtAfter(LogLevel.WARN, since));
        stats.put("unresolvedCount", logRepo.countByIsResolvedFalse());

        // Category stats
        Map<String, Long> catStats = new HashMap<>();
        logRepo.countByCategoryAndLevel(LogLevel.ERROR, since).forEach(row -> {
            catStats.put((String) row[0], (Long) row[1]);
        });
        stats.put("categoryStats", catStats);
        return stats;
    }

    public Map<String, Object> getLogContext(Long logId) {
        Map<String, Object> result = new HashMap<>();
        long start = Math.max(1, logId - 5);
        long end = logId + 5;
        result.put("context", logRepo.findContext(start, end));

        logRepo.findById(logId).ifPresent(entry -> {
            result.put("stackTrace", entry.getStackTrace());
        });
        return result;
    }

    public void resolveLog(Long logId) {
        logRepo.findById(logId).ifPresent(entry -> {
            entry.setIsResolved(true);
            logRepo.save(entry);
        });
    }

    @Scheduled(fixedRate = 30000) // every 30 seconds
    public void scanForAlerts() {
        LocalDateTime fiveMinAgo = LocalDateTime.now().minusMinutes(5);
        long recentErrors = logRepo.countByLogLevelAndCreatedAtAfter(LogLevel.ERROR, fiveMinAgo);
        if (recentErrors > 5) {
            log.warn("ALERT: {} ERROR logs in last 5 minutes!", recentErrors);
        }
    }
}
