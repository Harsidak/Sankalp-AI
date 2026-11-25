package com.sankalp.dashboard;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import com.sankalp.dashboard.DashboardDtos.DashboardSummary;
import com.sankalp.dashboard.DashboardDtos.HabitCompletion;
import com.sankalp.dashboard.DashboardDtos.MoodPoint;
import com.sankalp.dashboard.DashboardDtos.TagFrequency;
import com.sankalp.habits.HabitService;

// The dashboard is all counting and averaging, so we ask MySQL to do it with plain SQL
// (JdbcTemplate = run a SQL string, get rows back) instead of loading every row into Java.
@Service
public class DashboardService {

    private final JdbcTemplate jdbc;
    private final HabitService habitService;

    public DashboardService(JdbcTemplate jdbc, HabitService habitService) {
        this.jdbc = jdbc;
        this.habitService = habitService;
    }

    public DashboardSummary summary(String userId, int days) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(days - 1);

        // 1. mood per day. Days with no check-in stay null so the chart can show a gap.
        Map<LocalDate, double[]> byDay = new HashMap<>();
        jdbc.query("""
                select checkin_date, mood_score, energy_score from checkins
                where user_id = ? and checkin_date between ? and ?
                """,
                rs -> {
                    byDay.put(rs.getObject("checkin_date", LocalDate.class),
                            new double[] { rs.getInt("mood_score"), rs.getInt("energy_score") });
                },
                userId, start, end);

        List<MoodPoint> trend = new ArrayList<>();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            double[] scores = byDay.get(d);
            trend.add(new MoodPoint(d, scores == null ? null : scores[0], scores == null ? null : scores[1]));
        }

        // 2. averages and number of check-ins
        Map<String, Object> avg = jdbc.queryForMap("""
                select avg(mood_score) as mood, avg(energy_score) as energy, count(*) as total from checkins
                where user_id = ? and checkin_date between ? and ?
                """, userId, start, end);

        // 3. how many journal entries were written in the range
        Long journalCount = jdbc.queryForObject("""
                select count(*) from journal_entries
                where user_id = ? and date(created_at) between ? and ?
                """, Long.class, userId, start, end);

        // 4. most used tags (tags -> entry_tags -> journal_entries, counted per tag)
        List<TagFrequency> topTags = jdbc.query("""
                select t.name, t.color, count(*) as uses
                from tags t
                join entry_tags et on et.tag_id = t.id
                join journal_entries e on e.id = et.entry_id
                where t.user_id = ? and date(e.created_at) between ? and ?
                group by t.id, t.name, t.color
                order by uses desc, t.name asc
                limit 8
                """,
                (rs, i) -> new TagFrequency(rs.getString("name"), rs.getString("color"), rs.getLong("uses")),
                userId, start, end);

        // 5. completions per habit. LEFT JOIN keeps habits that were never done (0).
        List<HabitCompletion> habits = jdbc.query("""
                select h.id, h.name, h.color, h.target_per_week, count(l.id) as completions
                from habits h
                left join habit_logs l
                  on l.habit_id = h.id and l.completed_date between ? and ?
                where h.user_id = ? and h.is_archived = false
                group by h.id, h.name, h.color, h.target_per_week
                order by completions desc, h.name asc
                """,
                (rs, i) -> new HabitCompletion(
                        rs.getString("id"), rs.getString("name"), rs.getString("color"),
                        rs.getLong("completions"), rs.getInt("target_per_week"),
                        HabitService.currentStreak(habitService.completedDates(rs.getString("id")))),
                start, end, userId);

        int longestActive = habits.stream().mapToInt(HabitCompletion::currentStreak).max().orElse(0);

        return new DashboardSummary(days, trend,
                round(avg.get("mood")), round(avg.get("energy")), ((Number) avg.get("total")).longValue(),
                journalCount == null ? 0 : journalCount, topTags, habits, longestActive);
    }

    // MySQL gives back a BigDecimal (or null when there are no rows)
    static Double round(Object value) {
        return value == null ? null : Math.round(((Number) value).doubleValue() * 100) / 100.0;
    }
}
