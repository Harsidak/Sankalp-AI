package com.sankalp.habits;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// One row of the `habits` table. Habits are archived (isArchived = true), not deleted,
// so their history stays.
@Entity
@Table(name = "habits")
public class Habit {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String userId;
    public String name;
    public String icon;
    public String color = "#10b981";
    public int targetPerWeek = 7;
    public boolean isArchived = false;
    public Instant createdAt = Instant.now();
}
