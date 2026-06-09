package com.newgen.agent.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.newgen.agent.model.enums.LogLevel;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("system_logs")
public class SystemLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("service_name")
    private String serviceName;

    @TableField("log_level")
    private LogLevel logLevel;

    private String category;

    private String message;

    @TableField("stack_trace")
    private String stackTrace;

    @TableField("request_id")
    private String requestId;

    @TableField("session_id")
    private String sessionId;

    private String metadata;

    @TableField("is_resolved")
    private Boolean isResolved = false;

    @TableField(value = "created_at", fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
