package com.newgen.agent.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.newgen.agent.model.entity.Session;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SessionRepository extends BaseMapper<Session> {
}
