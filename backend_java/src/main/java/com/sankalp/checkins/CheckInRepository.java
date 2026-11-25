package com.sankalp.checkins;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface CheckInRepository extends JpaRepository<CheckIn, String> {

    Optional<CheckIn> findByUserIdAndCheckinDate(String userId, LocalDate checkinDate);

    // Oldest first, so the frontend can draw the trend line without re-sorting.
    List<CheckIn> findByUserIdAndCheckinDateBetweenOrderByCheckinDateAsc(String userId, LocalDate start,
            LocalDate end);

    Optional<CheckIn> findByIdAndUserId(String id, String userId);
}
