package com.sankalp.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class AuthDtos {

    public record RegisterRequest(
            @NotBlank @Email String email,
            @NotBlank @Size(min = 8, max = 128) String password,
            @Size(max = 255) String fullName) {
    }

    public record LoginRequest(@NotBlank @Email String email, @NotBlank String password) {
    }

    public record RefreshTokenRequest(@NotBlank String refreshToken) {
    }

    public record TokenResponse(String accessToken, String refreshToken, String tokenType, long expiresIn) {

        public TokenResponse(String accessToken, String refreshToken, long expiresIn) {
            this(accessToken, refreshToken, "bearer", expiresIn);
        }
    }

    public record AuthUserResponse(
            String id, String email, String fullName, String avatarUrl, String authProvider, boolean isVerified) {
    }
}
