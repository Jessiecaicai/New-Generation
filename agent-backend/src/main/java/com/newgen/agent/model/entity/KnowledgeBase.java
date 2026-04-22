package com.newgen.agent.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("knowledge_bases")
public class KnowledgeBase {

    @TableId(type = IdType.INPUT)
    private String id;

    private String name;

    private String description;

    @TableField("document_count")
    private Integer documentCount = 0;

    @TableField("chunk_count")
    private Integer chunkCount = 0;

    private String status = "ACTIVE";

    @TableField(value = "created_at", fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(value = "updated_at", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
