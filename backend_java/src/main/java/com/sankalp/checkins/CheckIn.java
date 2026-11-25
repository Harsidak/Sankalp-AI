package com.sankalp.checkins;

import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// One row of the `checkins` table: a mood/energy rating for one calendar day.
// The database has UNIQUE(user_id, checkin_date), so "once a day" is a real guarantee.
// The schema is owned by Alembic (ddl-auto=none), so the fields only describe how to
// read and write the existing columns.
@Entity
@Table(name = "checkins")
public class CheckIn {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String userId;
    public int moodScore;
    public int energyScore;
    public String note;
    public LocalDate checkinDate;
    public Instant createdAt = Instant.now();
}
