package com.newgen.agent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.model.enums.LogLevel;
import com.newgen.agent.repository.SystemLogRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
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
        if (logEntry.getId() == null) {
            logRepo.insert(logEntry);
        } else {
            logRepo.updateById(logEntry);
        }
        return logEntry;
    }

    /**
     * 分页查日志：按创建时间倒序（最新在前），同秒内按 id 倒序兜底。
     * page 为 0-based（兼容前端原有约定）；MP 内部是 1-based，自动 +1。
     */
    public IPage<SystemLog> getLogs(String level, int page, int size) {
        Page<SystemLog> pageable = new Page<>(page + 1L, size);
        LambdaQueryWrapper<SystemLog> qw = new LambdaQueryWrapper<SystemLog>()
                .orderByDesc(SystemLog::getCreatedAt)
                .orderByDesc(SystemLog::getId);
        if (level != null && !level.isBlank()) {
            qw.eq(SystemLog::getLogLevel, LogLevel.valueOf(level.toUpperCase()));
        }
        return logRepo.selectPage(pageable, qw);
    }

    public Map<String, Object> getStats(int hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(hours);
        Map<String, Object> stats = new HashMap<>();

        stats.put("errorCount", logRepo.selectCount(new LambdaQueryWrapper<SystemLog>()
                .eq(SystemLog::getLogLevel, LogLevel.ERROR)
                .gt(SystemLog::getCreatedAt, since)));

        stats.put("warnCount", logRepo.selectCount(new LambdaQueryWrapper<SystemLog>()
                .eq(SystemLog::getLogLevel, LogLevel.WARN)
                .gt(SystemLog::getCreatedAt, since)));

        stats.put("unresolvedCount", logRepo.selectCount(new LambdaQueryWrapper<SystemLog>()
                .eq(SystemLog::getIsResolved, false)));

        // Category stats
        Map<String, Long> catStats = new HashMap<>();
        for (Map<String, Object> row : logRepo.countByCategoryAndLevel(LogLevel.ERROR, since)) {
            Object cat = row.get("category");
            Object cnt = row.get("cnt");
            if (cat != null && cnt != null) {
                catStats.put(cat.toString(), ((Number) cnt).longValue());
            }
        }
        stats.put("categoryStats", catStats);
        return stats;
    }

    public Map<String, Object> getLogContext(Long logId) {
        Map<String, Object> result = new HashMap<>();
        long start = Math.max(1, logId - 5);
        long end = logId + 5;
        result.put("context", logRepo.findContext(start, end));

        SystemLog entry = logRepo.selectById(logId);
        if (entry != null) {
            result.put("stackTrace", entry.getStackTrace());
        }
        return result;
    }

    public void resolveLog(Long logId) {
        SystemLog entry = logRepo.selectById(logId);
        if (entry != null) {
            entry.setIsResolved(true);
            logRepo.updateById(entry);
        }
    }

    @Scheduled(fixedRate = 30000) // every 30 seconds
    public void scanForAlerts() {
        LocalDateTime fiveMinAgo = LocalDateTime.now().minusMinutes(5);
        Long recentErrors = logRepo.selectCount(new LambdaQueryWrapper<SystemLog>()
                .eq(SystemLog::getLogLevel, LogLevel.ERROR)
                .gt(SystemLog::getCreatedAt, fiveMinAgo));
        if (recentErrors != null && recentErrors > 5) {
            log.warn("ALERT: {} ERROR logs in last 5 minutes!", recentErrors);
        }
    }
}
