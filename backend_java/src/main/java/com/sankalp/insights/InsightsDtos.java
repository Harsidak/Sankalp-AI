package com.sankalp.insights;

import java.util.List;

public class InsightsDtos {

    // Average mood on days the habit was done vs not done. delta = done - missed (null if either side has no days)
    public record HabitMoodImpact(String habitId, String name, String color, long daysDone, long daysMissed,
            Double moodWhenDone, Double moodWhenMissed, Double delta) {
    }

    // weekday: 0 = Monday ... 6 = Sunday
    public record WeekdayMood(int weekday, String label, Double avgMood, Double avgEnergy, long checkins) {
    }

    public record MoodBucket(int score, long count) {
    }

    public record TagMood(String name, String color, long entries, Double avgMood) {
    }

    public record InsightsSummary(
            int rangeDays,
            List<HabitMoodImpact> habitImpact,
            List<WeekdayMood> weekday,
            List<MoodBucket> moodDistribution,
            List<TagMood> tagMood,
            String bestWeekday,
            String hardestWeekday,
            String headline) {
    }
}
