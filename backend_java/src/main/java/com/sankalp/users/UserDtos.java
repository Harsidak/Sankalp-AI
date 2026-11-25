package com.sankalp.users;

import java.time.Instant;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class UserDtos {

    public record UserRead(
            String id, String email, String fullName, String avatarUrl, String authProvider,
            boolean isActive, boolean isVerified, Instant createdAt, Instant updatedAt) {
    }

    // null = leave unchanged
    public record UserUpdate(@Size(max = 255) String fullName, String avatarUrl) {
    }

    public record ChangePasswordRequest(
            @NotBlank String currentPassword,
            @NotBlank @Size(min = 8, max = 128) String newPassword) {
    }
}
