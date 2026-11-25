package com.sankalp.habits;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface HabitLogRepository extends JpaRepository<HabitLog, String> {

    List<HabitLog> findByHabitId(String habitId);

    Optional<HabitLog> findByHabitIdAndCompletedDate(String habitId, LocalDate completedDate);
}
