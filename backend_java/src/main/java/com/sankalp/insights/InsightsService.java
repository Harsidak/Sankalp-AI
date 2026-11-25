package com.sankalp.insights;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import com.sankalp.insights.InsightsDtos.HabitMoodImpact;
import com.sankalp.insights.InsightsDtos.InsightsSummary;
import com.sankalp.insights.InsightsDtos.MoodBucket;
import com.sankalp.insights.InsightsDtos.TagMood;
import com.sankalp.insights.InsightsDtos.WeekdayMood;

// Dashboard = "what happened". Insights = "what is it connected to".
// Same idea as the dashboard: MySQL does the averaging, Java only shapes the result.
@Service
public class InsightsService {

    private static final String[] WEEKDAYS = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" };

    // Fewer days than this on either side is too little data to call it a pattern.
    private static final int MIN_DAYS = 4;

    private final JdbcTemplate jdbc;

    public InsightsService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public InsightsSummary summary(String userId, int days) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(days - 1);

        List<HabitMoodImpact> impacts = habitImpact(userId, start, end);
        List<WeekdayMood> weekdays = weekdayMood(userId, start, end);

        List<WeekdayMood> rated = weekdays.stream().filter(w -> w.avgMood() != null && w.checkins() >= 2).toList();
        String best = rated.stream().max(Comparator.comparing(WeekdayMood::avgMood)).map(WeekdayMood::label).orElse(null);
        String hardest = rated.stream().min(Comparator.comparing(WeekdayMood::avgMood)).map(WeekdayMood::label).orElse(null);

        return new InsightsSummary(days, impacts, weekdays, moodDistribution(userId, start, end),
                tagMood(userId, start, end), best, hardest, headline(impacts, rated));
    }

    // For every habit: average mood on check-in days where it was done vs. not done.
    //   habits JOIN checkins          -> every (habit, check-in day) pair
    //   LEFT JOIN habit_logs          -> a log row exists = done that day, NULL = not done
    // The last condition only counts days from when the habit started being tracked
    // (its first log or its creation day, whichever is earlier).
    private List<HabitMoodImpact> habitImpact(String userId, LocalDate start, LocalDate end) {
        List<HabitMoodImpact> list = jdbc.query("""
                select h.id, h.name, h.color,
                       count(case when l.id is not null then 1 end) as days_done,
                       count(case when l.id is null then 1 end) as days_missed,
                       avg(case when l.id is not null then c.mood_score end) as mood_done,
                       avg(case when l.id is null then c.mood_score end) as mood_missed
                from habits h
                join checkins c on c.user_id = h.user_id
                left join habit_logs l on l.habit_id = h.id and l.completed_date = c.checkin_date
                where h.user_id = ? and h.is_archived = false
                  and c.checkin_date between ? and ?
                  and c.checkin_date >= least(date(h.created_at),
                        coalesce((select min(completed_date) from habit_logs where habit_id = h.id), date(h.created_at)))
                group by h.id, h.name, h.color
                order by h.name
                """,
                (rs, i) -> {
                    Double done = round(rs.getObject("mood_done"));
                    Double missed = round(rs.getObject("mood_missed"));
                    Double delta = (done != null && missed != null) ? round(done - missed) : null;
                    return new HabitMoodImpact(rs.getString("id"), rs.getString("name"), rs.getString("color"),
                            rs.getLong("days_done"), rs.getLong("days_missed"), done, missed, delta);
                },
                userId, start, end);

        // Biggest positive effect first; habits without a delta go last.
        List<HabitMoodImpact> sorted = new ArrayList<>(list);
        sorted.sort(Comparator.comparing((HabitMoodImpact h) -> h.delta() == null)
                .thenComparing(h -> -(h.delta() == null ? 0 : h.delta())));
        return sorted;
    }

    // Average mood per day of the week. dayofweek(): 1 = Sunday ... 7 = Saturday, so (x + 5) % 7 gives Monday = 0.
    private List<WeekdayMood> weekdayMood(String userId, LocalDate start, LocalDate end) {
        Map<Integer, Map<String, Object>> byDay = new HashMap<>();
        jdbc.queryForList("""
                select (dayofweek(checkin_date) + 5) % 7 as weekday,
                       avg(mood_score) as avg_mood, avg(energy_score) as avg_energy, count(*) as checkins
                from checkins
                where user_id = ? and checkin_date between ? and ?
                group by weekday
                """, userId, start, end)
                .forEach(row -> byDay.put(((Number) row.get("weekday")).intValue(), row));

        List<WeekdayMood> result = new ArrayList<>();
        for (int i = 0; i < 7; i++) {
            Map<String, Object> row = byDay.get(i);
            result.add(row == null
                    ? new WeekdayMood(i, WEEKDAYS[i], null, null, 0)
                    : new WeekdayMood(i, WEEKDAYS[i], round(row.get("avg_mood")), round(row.get("avg_energy")),
                            ((Number) row.get("checkins")).longValue()));
        }
        return result;
    }

    // How many check-ins had mood 1, 2, 3, 4, 5 (zeros included).
    private List<MoodBucket> moodDistribution(String userId, LocalDate start, LocalDate end) {
        Map<Integer, Long> counts = new HashMap<>();
        jdbc.query("""
                select mood_score, count(*) as total from checkins
                where user_id = ? and checkin_date between ? and ?
                group by mood_score
                """,
                rs -> {
                    counts.put(rs.getInt("mood_score"), rs.getLong("total"));
                },
                userId, start, end);

        List<MoodBucket> result = new ArrayList<>();
        for (int score = 1; score <= 5; score++) {
            result.add(new MoodBucket(score, counts.getOrDefault(score, 0L)));
        }
        return result;
    }

    // Average mood on the days each tag was written about.
    // LEFT JOIN checkins: an entry written on a day without a check-in still counts as an entry.
    private List<TagMood> tagMood(String userId, LocalDate start, LocalDate end) {
        return jdbc.query("""
                select t.name, t.color, count(distinct e.id) as entries, avg(c.mood_score) as avg_mood
                from tags t
                join entry_tags et on et.tag_id = t.id
                join journal_entries e on e.id = et.entry_id
                left join checkins c on c.user_id = t.user_id and c.checkin_date = date(e.created_at)
                where t.user_id = ? and date(e.created_at) between ? and ?
                group by t.id, t.name, t.color
                order by entries desc, t.name asc
                limit 8
                """,
                (rs, i) -> new TagMood(rs.getString("name"), rs.getString("color"), rs.getLong("entries"),
                        round(rs.getObject("avg_mood"))),
                userId, start, end);
    }

    // One sentence about the strongest pattern, or null if the data is too thin.
    // Built straight from the numbers (no AI), so it cannot make things up.
    private String headline(List<HabitMoodImpact> impacts, List<WeekdayMood> rated) {
        HabitMoodImpact strongest = impacts.stream()
                .filter(h -> h.delta() != null && h.daysDone() >= MIN_DAYS && h.daysMissed() >= MIN_DAYS)
                .max(Comparator.comparing(h -> Math.abs(h.delta())))
                .orElse(null);
        if (strongest != null && Math.abs(strongest.delta()) >= 0.3) {
            String direction = strongest.delta() > 0 ? "higher" : "lower";
            return String.format("Your mood runs %.1f points %s on days you keep “%s”.",
                    Math.abs(strongest.delta()), direction, strongest.name());
        }

        if (rated.size() >= 3) {
            WeekdayMood best = rated.stream().max(Comparator.comparing(WeekdayMood::avgMood)).get();
            WeekdayMood worst = rated.stream().min(Comparator.comparing(WeekdayMood::avgMood)).get();
            if (best.avgMood() - worst.avgMood() >= 0.4) {
                return best.label() + "s read best for you; " + worst.label() + "s are the hardest.";
            }
        }
        return null;
    }

    // MySQL gives back a BigDecimal (or null when there is nothing to average)
    private static Double round(Object value) {
        return value == null ? null : Math.round(((Number) value).doubleValue() * 100) / 100.0;
    }
}
