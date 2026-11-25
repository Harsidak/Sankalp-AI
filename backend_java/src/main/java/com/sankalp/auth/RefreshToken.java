package com.sankalp.auth;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// Only a SHA-256 hash of the refresh token is stored. Rotation and logout set
// is_revoked, so a replayed old token is refused on the next refresh.
@Entity
@Table(name = "refresh_tokens")
public class RefreshToken {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String tokenHash;
    public String userId;
    public boolean isRevoked = false;
    public Instant expiresAt;
    public Instant createdAt = Instant.now();
}
