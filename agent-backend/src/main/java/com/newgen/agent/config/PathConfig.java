package com.newgen.agent.config;

import jakarta.annotation.PostConstruct;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.nio.file.Paths;

@Data
@Configuration
@ConfigurationProperties(prefix = "agent.paths")
public class PathConfig {
    private String dataRoot = "/data";
    private String knowledgeUploadDir;
    private String logDir;
    private String logScanDir;
    private String exportDir;
    private String tempDir;
    private int knowledgeMaxFileSizeMb = 50;
    private String knowledgeAllowedExtensions = ".pdf,.txt,.md,.docx";
    private int tempCleanupHours = 24;

    @PostConstruct
    public void init() {
        if (knowledgeUploadDir == null) knowledgeUploadDir = dataRoot + "/knowledge/uploads";
        if (logDir == null) logDir = dataRoot + "/logs/java";
        if (logScanDir == null) logScanDir = dataRoot + "/logs";
        if (exportDir == null) exportDir = dataRoot + "/export";
        if (tempDir == null) tempDir = dataRoot + "/temp";

        for (String dir : new String[]{knowledgeUploadDir, logDir, exportDir, tempDir}) {
            Paths.get(dir).toFile().mkdirs();
        }
    }
}
