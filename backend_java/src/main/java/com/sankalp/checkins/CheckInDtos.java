package com.sankalp.checkins;

import java.time.Instant;
import java.time.LocalDate;

import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

public class CheckInDtos {

    // A missing score arrives as 0 and is rejected by @Min, just like FastAPI's ge=1.
    public record CheckInCreate(
            @Min(1) @Max(5) int moodScore,
            @Min(1) @Max(5) int energyScore,
            @Size(max = 2000) String note,
            LocalDate checkinDate) {

        // Same rule as the Python schema: past days are fine, future days are not.
        // @JsonIgnore keeps this validator method out of the JSON response.
        @AssertTrue(message = "checkin_date cannot be in the future")
        @JsonIgnore
        public boolean isCheckinDateNotInFuture() {
            return checkinDate == null || !checkinDate.isAfter(LocalDate.now());
        }
    }

    // Any field may be null = "leave unchanged" (the same convention as habits/tags).
    public record CheckInUpdate(
            @Min(1) @Max(5) Integer moodScore,
            @Min(1) @Max(5) Integer energyScore,
            @Size(max = 2000) String note) {
    }

    public record CheckInRead(
            String id, int moodScore, int energyScore, String note, LocalDate checkinDate, Instant createdAt) {
    }

    public record StreakRead(int currentStreak, int longestStreak, boolean checkedInToday) {
    }
}
