package com.sankalp.habits;

import java.time.LocalDate;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.common.NotFoundException;
import com.sankalp.habits.HabitDtos.HabitCreate;
import com.sankalp.habits.HabitDtos.HabitLogResult;
import com.sankalp.habits.HabitDtos.HabitRead;
import com.sankalp.habits.HabitDtos.HabitUpdate;

@Service
@Transactional
public class HabitService {

    private final HabitRepository habits;
    private final HabitLogRepository logs;

    public HabitService(HabitRepository habits, HabitLogRepository logs) {
        this.habits = habits;
        this.logs = logs;
    }

    public List<HabitRead> list(String userId, boolean includeArchived) {
        List<Habit> found = includeArchived
                ? habits.findByUserIdOrderByCreatedAtAsc(userId)
                : habits.findByUserIdAndIsArchivedFalseOrderByCreatedAtAsc(userId);
        return found.stream().map(this::toRead).toList();
    }

    public HabitRead get(String userId, String habitId) {
        return toRead(getOwned(userId, habitId));
    }

    public HabitRead create(String userId, HabitCreate data) {
        Habit habit = new Habit();
        habit.userId = userId;
        habit.name = data.name();
        habit.icon = data.icon();
        if (data.color() != null) {
            habit.color = data.color();
        }
        if (data.targetPerWeek() != null) {
            habit.targetPerWeek = data.targetPerWeek();
        }
        habits.save(habit);
        return toRead(habit);
    }

    public HabitRead update(String userId, String habitId, HabitUpdate data) {
        Habit habit = getOwned(userId, habitId);
        if (data.name() != null) {
            habit.name = data.name();
        }
        if (data.icon() != null) {
            habit.icon = data.icon();
        }
        if (data.color() != null) {
            habit.color = data.color();
        }
        if (data.targetPerWeek() != null) {
            habit.targetPerWeek = data.targetPerWeek();
        }
        if (data.isArchived() != null) {
            habit.isArchived = data.isArchived();
        }
        return toRead(habit);
    }

    // The habit's logs are removed by the database (ON DELETE CASCADE).
    public void delete(String userId, String habitId) {
        habits.delete(getOwned(userId, habitId));
    }

    // One endpoint for both directions: done -> undo, not done -> done.
    public HabitLogResult toggle(String userId, String habitId, LocalDate date) {
        Habit habit = getOwned(userId, habitId);
        LocalDate day = date != null ? date : LocalDate.now();

        var existing = logs.findByHabitIdAndCompletedDate(habit.id, day);
        boolean completed;
        if (existing.isPresent()) {
            logs.delete(existing.get());
            completed = false;
        } else {
            HabitLog log = new HabitLog();
            log.habitId = habit.id;
            log.completedDate = day;
            logs.save(log);
            completed = true;
        }

        logs.flush(); // write now, so the next query sees the change
        List<LocalDate> dates = completedDates(habit.id);
        return new HabitLogResult(habit.id, day, completed, currentStreak(dates), longestStreak(dates));
    }

    // ---------- streaks (plain functions, no database) ----------

    // Consecutive days ending today (or yesterday, so the streak is not "broken" before you tick today).
    public static int currentStreak(Collection<LocalDate> completed) {
        Set<LocalDate> days = new HashSet<>(completed);
        LocalDate today = LocalDate.now();
        LocalDate cursor;
        if (days.contains(today)) {
            cursor = today;
        } else if (days.contains(today.minusDays(1))) {
            cursor = today.minusDays(1);
        } else {
            return 0;
        }

        int streak = 0;
        while (days.contains(cursor)) {
            streak++;
            cursor = cursor.minusDays(1);
        }
        return streak;
    }

    // Longest run of consecutive days, ever.
    public static int longestStreak(Collection<LocalDate> completed) {
        List<LocalDate> days = completed.stream().distinct().sorted().toList();
        int longest = days.isEmpty() ? 0 : 1;
        int run = 1;
        for (int i = 1; i < days.size(); i++) {
            if (days.get(i - 1).plusDays(1).equals(days.get(i))) {
                run++;
                longest = Math.max(longest, run);
            } else {
                run = 1;
            }
        }
        return longest;
    }

    // Also used by the dashboard
    public List<LocalDate> completedDates(String habitId) {
        return logs.findByHabitId(habitId).stream().map(l -> l.completedDate).sorted().toList();
    }

    private Habit getOwned(String userId, String habitId) {
        return habits.findByIdAndUserId(habitId, userId)
                .orElseThrow(() -> new NotFoundException("Habit not found"));
    }

    private HabitRead toRead(Habit h) {
        List<LocalDate> dates = completedDates(h.id);
        return new HabitRead(h.id, h.name, h.icon, h.color, h.targetPerWeek, h.isArchived, h.createdAt,
                dates, currentStreak(dates), longestStreak(dates), dates.contains(LocalDate.now()));
    }
}
