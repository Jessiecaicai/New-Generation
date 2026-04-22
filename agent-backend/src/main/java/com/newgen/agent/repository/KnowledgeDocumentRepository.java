package com.newgen.agent.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.newgen.agent.model.entity.KnowledgeDocument;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface KnowledgeDocumentRepository extends BaseMapper<KnowledgeDocument> {
}
