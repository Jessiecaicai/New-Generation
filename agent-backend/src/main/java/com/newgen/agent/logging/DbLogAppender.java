package com.newgen.agent.logging;

import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.classic.spi.IThrowableProxy;
import ch.qos.logback.classic.spi.ThrowableProxyUtil;
import ch.qos.logback.core.AppenderBase;
import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.model.enums.LogLevel;
import com.newgen.agent.repository.SystemLogRepository;
import org.slf4j.MDC;
import org.springframework.context.ApplicationContext;

import java.time.LocalDateTime;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

/**
 * 自定义 Logback Appender：将 WARN/ERROR/FATAL 级别日志写入数据库。
 * 使用异步队列避免阻塞主线程。
 */
public class DbLogAppender extends AppenderBase<ILoggingEvent> {

    private static ApplicationContext applicationContext;
    private SystemLogRepository logRepository;
    private final BlockingQueue<SystemLog> queue = new ArrayBlockingQueue<>(500);
    private Thread consumerThread;
    private volatile boolean running = true;

    /**
     * Spring 启动时注入 ApplicationContext
     */
    public static void setApplicationContext(ApplicationContext ctx) {
        applicationContext = ctx;
    }

    @Override
    public void start() {
        super.start();
        // 启动消费线程，批量写入数据库
        consumerThread = new Thread(this::consumeLoop, "db-log-writer");
        consumerThread.setDaemon(true);
        consumerThread.start();
    }

    @Override
    public void stop() {
        running = false;
        if (consumerThread != null) {
            consumerThread.interrupt();
        }
        // 清空队列中的剩余日志
        flushQueue();
        super.stop();
    }

    @Override
    protected void append(ILoggingEvent event) {
        // 只记录 WARN 及以上
        if (event.getLevel().toInt() < ch.qos.logback.classic.Level.WARN_INT) {
            return;
        }

        // 避免循环日志（DbLogAppender 自身写入不再入库）
        if (event.getLoggerName().contains("DbLogAppender") ||
            event.getLoggerName().contains("SystemLogRepository")) {
            return;
        }

        try {
            SystemLog log = new SystemLog();
            log.setServiceName("JAVA_BACKEND");
            log.setLogLevel(mapLevel(event.getLevel()));
            log.setCategory(extractCategory(event.getLoggerName()));
            log.setMessage(event.getFormattedMessage());
            log.setCreatedAt(LocalDateTime.now());
            log.setIsResolved(false);

            // 堆栈信息
            IThrowableProxy throwable = event.getThrowableProxy();
            if (throwable != null) {
                String stackTrace = ThrowableProxyUtil.asString(throwable);
                // 限制堆栈长度
                if (stackTrace.length() > 4000) {
                    stackTrace = stackTrace.substring(0, 4000) + "\n... (truncated)";
                }
                log.setStackTrace(stackTrace);
            }

            // MDC 中的请求上下文
            log.setRequestId(MDC.get("requestId"));
            log.setSessionId(MDC.get("sessionId"));

            // 非阻塞入队
            if (!queue.offer(log)) {
                // 队列满了，丢弃最旧的
                queue.poll();
                queue.offer(log);
            }
        } catch (Exception e) {
            // 避免日志写入异常导致应用崩溃
            addError("Failed to queue log entry", e);
        }
    }

    private void consumeLoop() {
        while (running) {
            try {
                SystemLog log = queue.take(); // 阻塞等待
                ensureRepository();
                if (logRepository != null) {
                    logRepository.save(log);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                // 数据库写入失败，等一会再试
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
    }

    private void flushQueue() {
        ensureRepository();
        if (logRepository == null) return;
        SystemLog log;
        while ((log = queue.poll()) != null) {
            try {
                logRepository.save(log);
            } catch (Exception ignored) {
            }
        }
    }

    private void ensureRepository() {
        if (logRepository == null && applicationContext != null) {
            try {
                logRepository = applicationContext.getBean(SystemLogRepository.class);
            } catch (Exception ignored) {
            }
        }
    }

    private LogLevel mapLevel(ch.qos.logback.classic.Level level) {
        return switch (level.toInt()) {
            case ch.qos.logback.classic.Level.ERROR_INT -> LogLevel.ERROR;
            case ch.qos.logback.classic.Level.WARN_INT -> LogLevel.WARN;
            default -> LogLevel.INFO;
        };
    }

    private String extractCategory(String loggerName) {
        if (loggerName == null) return "UNKNOWN";
        // 取最后一段类名作为分类
        int lastDot = loggerName.lastIndexOf('.');
        return lastDot > 0 ? loggerName.substring(lastDot + 1) : loggerName;
    }
}
