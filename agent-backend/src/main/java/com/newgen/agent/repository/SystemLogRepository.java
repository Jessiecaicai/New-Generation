package com.newgen.agent.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.newgen.agent.model.entity.SystemLog;
import com.newgen.agent.model.enums.LogLevel;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface SystemLogRepository extends BaseMapper<SystemLog> {

    @Select("SELECT * FROM system_logs WHERE id BETWEEN #{start} AND #{end} ORDER BY id")
    List<SystemLog> findContext(@Param("start") Long start, @Param("end") Long end);

    @Select("SELECT category AS category, COUNT(*) AS cnt FROM system_logs "
            + "WHERE log_level = #{level} AND created_at > #{after} GROUP BY category")
    List<Map<String, Object>> countByCategoryAndLevel(@Param("level") LogLevel level,
                                                      @Param("after") LocalDateTime after);
}
