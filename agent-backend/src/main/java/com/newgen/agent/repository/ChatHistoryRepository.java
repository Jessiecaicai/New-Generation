package com.newgen.agent.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.newgen.agent.model.entity.ChatHistory;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatHistoryRepository extends BaseMapper<ChatHistory> {
}
