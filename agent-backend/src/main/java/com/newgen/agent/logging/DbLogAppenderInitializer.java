package com.newgen.agent.logging;

import jakarta.annotation.PostConstruct;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;

/**
 * Spring 启动后，将 ApplicationContext 注入到 DbLogAppender 中，
 * 使其能够获取 SystemLogRepository bean。
 */
@Component
public class DbLogAppenderInitializer {

    private final ApplicationContext applicationContext;

    public DbLogAppenderInitializer(ApplicationContext applicationContext) {
        this.applicationContext = applicationContext;
    }

    @PostConstruct
    public void init() {
        DbLogAppender.setApplicationContext(applicationContext);
    }
}
