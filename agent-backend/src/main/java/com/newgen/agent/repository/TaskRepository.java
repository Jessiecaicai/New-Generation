package com.newgen.agent.repository;

import com.newgen.agent.model.entity.Task;
import com.newgen.agent.model.enums.TaskStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TaskRepository extends JpaRepository<Task, String> {
    List<Task> findByStatus(TaskStatus status);
    long countByStatus(TaskStatus status);
}
