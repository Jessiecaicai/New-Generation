package com.newgen.agent.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("chat_history")
public class ChatHistory {

    @TableId(type = IdType.INPUT)
    private String id;

    @TableField("session_id")
    private String sessionId;

    private Role role;

    private String content;

    private String intent;

    private String metadata;

    @TableField(value = "created_at", fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    public enum Role { USER, ASSISTANT }
}
