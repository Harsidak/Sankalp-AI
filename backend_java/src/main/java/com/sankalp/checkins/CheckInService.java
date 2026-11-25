package com.sankalp.checkins;

import java.time.LocalDate;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.checkins.CheckInDtos.CheckInCreate;
import com.sankalp.checkins.CheckInDtos.CheckInRead;
import com.sankalp.checkins.CheckInDtos.CheckInUpdate;
import com.sankalp.checkins.CheckInDtos.StreakRead;
import com.sankalp.common.NotFoundException;
import com.sankalp.habits.HabitService;

@Service
@Transactional
public class CheckInService {

    // The streak endpoint looks back one year, as the Python router does.
    private static final int MAX_RANGE_DAYS = 365;

    private final CheckInRepository checkins;

    public CheckInService(CheckInRepository checkins) {
        this.checkins = checkins;
    }

    // An explicit start+end wins; otherwise the last `days` days are used.
    public List<CheckInRead> list(String userId, LocalDate start, LocalDate end, int days) {
        LocalDate from;
        LocalDate to;
        if (start != null && end != null) {
            from = start;
            to = end;
        } else {
            to = LocalDate.now();
            int safeDays = Math.min(Math.max(days, 1), MAX_RANGE_DAYS);
            from = to.minusDays(safeDays - 1L);
        }
        return checkins.findByUserIdAndCheckinDateBetweenOrderByCheckinDateAsc(userId, from, to)
                .stream().map(this::toRead).toList();
    }

    // null (not 404) means "not checked in yet" — the UI treats that as a normal state.
    public CheckInRead today(String userId) {
        return checkins.findByUserIdAndCheckinDate(userId, LocalDate.now())
                .map(this::toRead)
                .orElse(null);
    }

    // Current run anchored on today/yesterday; longest run anywhere in the last year.
    // Reuses the exact streak functions the habits module already uses.
    public StreakRead streak(String userId) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(MAX_RANGE_DAYS - 1L);
        Set<LocalDate> days = checkins.findByUserIdAndCheckinDateBetweenOrderByCheckinDateAsc(userId, start, end)
                .stream()
                .map(c -> c.checkinDate)
                .collect(Collectors.toSet());
        return new StreakRead(HabitService.currentStreak(days), HabitService.longestStreak(days), days.contains(end));
    }

    // Posting twice for the same day re-rates the existing check-in (idempotent).
    public CheckInRead createOrUpdate(String userId, CheckInCreate data) {
        LocalDate day = data.checkinDate() != null ? data.checkinDate() : LocalDate.now();
        CheckIn checkin = checkins.findByUserIdAndCheckinDate(userId, day).orElseGet(() -> {
            CheckIn fresh = new CheckIn();
            fresh.userId = userId;
            fresh.checkinDate = day;
            return fresh;
        });
        checkin.moodScore = data.moodScore();
        checkin.energyScore = data.energyScore();
        checkin.note = data.note();
        return toRead(checkins.save(checkin));
    }

    public CheckInRead update(String userId, String checkinId, CheckInUpdate data) {
        CheckIn checkin = getOwned(userId, checkinId);
        if (data.moodScore() != null) {
            checkin.moodScore = data.moodScore();
        }
        if (data.energyScore() != null) {
            checkin.energyScore = data.energyScore();
        }
        if (data.note() != null) {
            checkin.note = data.note();
        }
        return toRead(checkin); // dirty checking writes it when the transaction ends
    }

    public void delete(String userId, String checkinId) {
        checkins.delete(getOwned(userId, checkinId));
    }

    // Someone else's check-in looks exactly like a missing one.
    private CheckIn getOwned(String userId, String checkinId) {
        return checkins.findByIdAndUserId(checkinId, userId)
                .orElseThrow(() -> new NotFoundException("Check-in not found"));
    }

    private CheckInRead toRead(CheckIn c) {
        return new CheckInRead(c.id, c.moodScore, c.energyScore, c.note, c.checkinDate, c.createdAt);
    }
}
