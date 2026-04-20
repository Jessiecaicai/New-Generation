package com.newgen.agent.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.core.JdbcTemplate;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

import javax.sql.DataSource;

/**
 * 双数据源配置：
 * - 主数据源 (Primary): agent_meta 库，JPA 使用，可读写
 * - 业务数据源: business_db 库，SQL 查询使用，只读
 */
@Configuration
public class BusinessDataSourceConfig {

    // ===== 主数据源（agent_meta）标记为 Primary，给 JPA 用 =====
    @Bean
    @Primary
    @ConfigurationProperties("spring.datasource")
    public DataSourceProperties primaryDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    @Primary
    public DataSource dataSource() {
        return primaryDataSourceProperties()
                .initializeDataSourceBuilder()
                .build();
    }

    // ===== 业务数据源（business_db）只读 =====
    @Value("${agent.business-datasource.url:jdbc:mysql://localhost:3306/business_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai}")
    private String businessUrl;

    @Value("${agent.business-datasource.username:root}")
    private String businessUsername;

    @Value("${agent.business-datasource.password:pp0123456}")
    private String businessPassword;

    @Bean(name = "businessDataSource")
    public DataSource businessDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(businessUrl);
        config.setUsername(businessUsername);
        config.setPassword(businessPassword);
        config.setMaximumPoolSize(10);
        config.setMinimumIdle(3);
        config.setReadOnly(true);
        config.setPoolName("business-pool");
        return new HikariDataSource(config);
    }

    @Bean(name = "businessJdbcTemplate")
    public JdbcTemplate businessJdbcTemplate() {
        return new JdbcTemplate(businessDataSource());
    }
}
