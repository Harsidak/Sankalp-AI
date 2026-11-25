package com.sankalp.habits;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public class HabitDtos {

    static final String HEX = "^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$";

    public record HabitCreate(
            @NotBlank @Size(max = 100) String name,
            @Size(max = 50) String icon,
            @Pattern(regexp = HEX) String color,
            @Min(1) @Max(7) Integer targetPerWeek) {
    }

    // Any field may be null = "leave unchanged"
    public record HabitUpdate(
            @Size(min = 1, max = 100) String name,
            @Size(max = 50) String icon,
            @Pattern(regexp = HEX) String color,
            @Min(1) @Max(7) Integer targetPerWeek,
            Boolean isArchived) {
    }

    // Stored columns + values calculated from the logs (dates, streaks)
    public record HabitRead(
            String id, String name, String icon, String color, int targetPerWeek, boolean isArchived,
            Instant createdAt,
            List<LocalDate> completedDates, int currentStreak, int longestStreak, boolean completedToday) {
    }

    // completedDate is optional: null means today
    public record HabitLogToggle(LocalDate completedDate) {
    }

    public record HabitLogResult(
            String habitId, LocalDate completedDate, boolean completed, int currentStreak, int longestStreak) {
    }
}
