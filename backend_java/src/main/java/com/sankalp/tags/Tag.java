package com.sankalp.tags;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// One row of the `tags` table. The fields are public only to keep the file short.
// Java names are camelCase; Spring maps userId -> user_id, createdAt -> created_at.
// The table has UNIQUE(user_id, name), so a user cannot have two tags with the same name.
@Entity
@Table(name = "tags")
public class Tag {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String userId;
    public String name;
    public String color = "#6366f1";
    public Instant createdAt = Instant.now();
}
