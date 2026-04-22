package com.newgen.agent.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.newgen.agent.model.enums.TaskStatus;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("tasks")
public class Task {

    @TableId(type = IdType.INPUT)
    private String id;

    @TableField("session_id")
    private String sessionId;

    private String question;

    private TaskStatus status = TaskStatus.QUEUED;

    private String intent;

    private String result;

    @TableField("error_message")
    private String errorMessage;

    @TableField("queue_position")
    private Integer queuePosition;

    @TableField(value = "created_at", fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField("started_at")
    private LocalDateTime startedAt;

    @TableField("completed_at")
    private LocalDateTime completedAt;
}
