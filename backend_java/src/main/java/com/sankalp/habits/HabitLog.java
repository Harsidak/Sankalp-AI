package com.sankalp.habits;

import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// "Habit was done on this day" = one row. Marking done = insert, undo = delete.
// The table has UNIQUE(habit_id, completed_date), so a day can never be logged twice.
@Entity
@Table(name = "habit_logs")
public class HabitLog {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String habitId;
    public LocalDate completedDate;
    public Instant createdAt = Instant.now();
}
