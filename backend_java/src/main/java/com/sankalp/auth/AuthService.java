package com.sankalp.auth;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Locale;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.auth.AuthDtos.AuthUserResponse;
import com.sankalp.auth.AuthDtos.LoginRequest;
import com.sankalp.auth.AuthDtos.RefreshTokenRequest;
import com.sankalp.auth.AuthDtos.RegisterRequest;
import com.sankalp.auth.AuthDtos.TokenResponse;
import com.sankalp.common.AuthenticationException;
import com.sankalp.common.NotFoundException;
import com.sankalp.users.User;
import com.sankalp.users.UserRepository;
import com.sankalp.users.UserService;

import io.jsonwebtoken.Claims;

@Service
@Transactional
public class AuthService {

    private static final String LOCAL = "local";

    private final UserRepository users;
    private final UserService userService;
    private final RefreshTokenRepository refreshTokens;
    private final JwtService jwt;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public AuthService(UserRepository users, UserService userService, RefreshTokenRepository refreshTokens,
            JwtService jwt) {
        this.users = users;
        this.userService = userService;
        this.refreshTokens = refreshTokens;
        this.jwt = jwt;
    }

    public TokenResponse register(RegisterRequest data) {
        User user = userService.createUser(normalize(data.email()), data.password(), data.fullName(),
                null, LOCAL, null, false);
        return issue(user.id);
    }

    public TokenResponse login(LoginRequest data) {
        User user = users.findByEmail(normalize(data.email()))
                .orElseThrow(() -> new AuthenticationException("Invalid email or password"));
        if (user.hashedPassword == null || user.hashedPassword.isBlank()) {
            throw new AuthenticationException("This account uses Google sign-in. Please log in with Google.");
        }
        if (!encoder.matches(data.password(), user.hashedPassword)) {
            throw new AuthenticationException("Invalid email or password");
        }
        if (!user.isActive) {
            throw new AuthenticationException("Account is deactivated");
        }
        return issue(user.id);
    }

    // Rotation: the old refresh token is revoked and a new pair is issued.
    public TokenResponse refresh(RefreshTokenRequest data) {
        String token = data.refreshToken();
        Claims claims;
        try {
            claims = jwt.parse(token);
        } catch (RuntimeException e) {
            throw new AuthenticationException("Invalid or expired refresh token");
        }
        if (!"refresh".equals(jwt.typeOf(claims))) {
            throw new AuthenticationException("Invalid or expired refresh token");
        }
        String userId = claims.getSubject();
        if (userId == null || userId.isBlank()) {
            throw new AuthenticationException("Invalid token payload");
        }

        RefreshToken stored = refreshTokens.findByTokenHash(sha256(token))
                .orElseThrow(() -> new AuthenticationException("Refresh token has been revoked"));
        if (stored.expiresAt != null && stored.expiresAt.isBefore(Instant.now())) {
            throw new AuthenticationException("Refresh token has expired");
        }
        stored.isRevoked = true;
        return issue(userId);
    }

    // Unknown tokens are ignored: logout is always safe to call.
    public void logout(RefreshTokenRequest data) {
        refreshTokens.findByTokenHash(sha256(data.refreshToken())).ifPresent(t -> t.isRevoked = true);
    }

    public AuthUserResponse me(String userId) {
        User user = users.findById(userId).orElseThrow(() -> new NotFoundException("User not found"));
        return new AuthUserResponse(user.id, user.email, user.fullName, user.avatarUrl,
                user.authProvider, user.isVerified);
    }

    private TokenResponse issue(String userId) {
        String access = jwt.accessToken(userId);
        String refresh = jwt.refreshToken(userId);
        RefreshToken stored = new RefreshToken();
        stored.userId = userId;
        stored.tokenHash = sha256(refresh);
        stored.expiresAt = jwt.refreshExpiry();
        refreshTokens.save(stored);
        return new TokenResponse(access, refresh, jwt.accessTtlSeconds());
    }

    private static String normalize(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }

    private static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
