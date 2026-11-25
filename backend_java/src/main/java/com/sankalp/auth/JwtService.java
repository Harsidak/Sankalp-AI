package com.sankalp.auth;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;

import javax.crypto.SecretKey;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

// HS256 tokens with the same claims the Python backend writes:
// sub = user id, type = access|refresh, exp, iat, and jti on refresh tokens.
// Using the same secret therefore makes tokens from either backend readable.
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.access-token-minutes:15}")
    private long accessMinutes;

    @Value("${jwt.refresh-token-days:7}")
    private long refreshDays;

    public String accessToken(String userId) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(userId)
                .claim("type", "access")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(accessMinutes * 60)))
                .signWith(key(), Jwts.SIG.HS256)
                .compact();
    }

    public String refreshToken(String userId) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(userId)
                .id(UUID.randomUUID().toString()) // jti: two tokens in one second must not collide
                .claim("type", "refresh")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(refreshDays * 86400)))
                .signWith(key(), Jwts.SIG.HS256)
                .compact();
    }

    // Throws JwtException / IllegalArgumentException when invalid or expired.
    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key()).build().parseSignedClaims(token).getPayload();
    }

    public String typeOf(Claims claims) {
        return claims.get("type", String.class);
    }

    public long accessTtlSeconds() {
        return accessMinutes * 60;
    }

    public Instant refreshExpiry() {
        return Instant.now().plusSeconds(refreshDays * 86400);
    }

    private SecretKey key() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
