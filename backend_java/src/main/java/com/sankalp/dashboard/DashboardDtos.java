package com.sankalp.dashboard;

import java.time.LocalDate;
import java.util.List;

public class DashboardDtos {

    // One day on the mood chart. mood/energy are null on days without a check-in.
    public record MoodPoint(LocalDate day, Double mood, Double energy) {
    }

    public record TagFrequency(String name, String color, long count) {
    }

    public record HabitCompletion(String habitId, String name, String color, long completions, int target,
            int currentStreak) {
    }

    public record DashboardSummary(
            int rangeDays,
            List<MoodPoint> moodTrend,
            Double averageMood,
            Double averageEnergy,
            long checkinCount,
            long journalCount,
            List<TagFrequency> topTags,
            List<HabitCompletion> habitCompletions,
            int longestActiveStreak) {
    }
}
