package com.sankalp.habits;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface HabitRepository extends JpaRepository<Habit, String> {

    List<Habit> findByUserIdOrderByCreatedAtAsc(String userId);

    List<Habit> findByUserIdAndIsArchivedFalseOrderByCreatedAtAsc(String userId);

    Optional<Habit> findByIdAndUserId(String id, String userId);
}
