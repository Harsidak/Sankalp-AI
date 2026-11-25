package com.sankalp.users;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// One row of the `users` table (created by Alembic on the Python side).
// hashed_password is nullable for Google-only accounts.
@Entity
@Table(name = "users")
public class User {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String email;
    public String hashedPassword;
    public String fullName;
    public String avatarUrl;
    public boolean isActive = true;
    public boolean isVerified = false;
    public String authProvider = "local";
    public String googleId;
    public Instant createdAt = Instant.now();
    public Instant updatedAt = Instant.now();
}
