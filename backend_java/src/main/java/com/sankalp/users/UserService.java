package com.sankalp.users;

import java.time.Instant;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.common.AuthenticationException;
import com.sankalp.common.ConflictException;
import com.sankalp.common.NotFoundException;
import com.sankalp.users.UserDtos.ChangePasswordRequest;
import com.sankalp.users.UserDtos.UserRead;
import com.sankalp.users.UserDtos.UserUpdate;

@Service
@Transactional
public class UserService {

    private final UserRepository users;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public UserService(UserRepository users) {
        this.users = users;
    }

    // Used by auth registration (local) and, later, Google sign-in.
    public User createUser(String email, String password, String fullName, String avatarUrl,
            String authProvider, String googleId, boolean isVerified) {
        if (users.findByEmail(email).isPresent()) {
            throw new ConflictException("An account with this email already exists");
        }
        User user = new User();
        user.email = email;
        user.hashedPassword = (password == null || password.isBlank()) ? null : encoder.encode(password);
        user.fullName = fullName;
        user.avatarUrl = avatarUrl;
        user.authProvider = authProvider;
        user.googleId = googleId;
        user.isVerified = isVerified;
        return users.save(user);
    }

    public UserRead profile(String userId) {
        return toRead(get(userId));
    }

    public UserRead updateProfile(String userId, UserUpdate data) {
        User user = get(userId);
        if (data.fullName() != null) {
            user.fullName = data.fullName();
        }
        if (data.avatarUrl() != null) {
            user.avatarUrl = data.avatarUrl();
        }
        user.updatedAt = Instant.now();
        return toRead(user);
    }

    // BCryptPasswordEncoder also verifies the $2b$ hashes written by Python's passlib.
    public void changePassword(String userId, ChangePasswordRequest data) {
        User user = get(userId);
        if (user.hashedPassword == null || user.hashedPassword.isBlank()) {
            throw new ConflictException("Cannot change password for OAuth-only accounts. Please set a password first.");
        }
        if (!encoder.matches(data.currentPassword(), user.hashedPassword)) {
            throw new AuthenticationException("Current password is incorrect");
        }
        user.hashedPassword = encoder.encode(data.newPassword());
        user.updatedAt = Instant.now();
    }

    private User get(String userId) {
        return users.findById(userId).orElseThrow(() -> new NotFoundException("User not found"));
    }

    private UserRead toRead(User user) {
        return new UserRead(user.id, user.email, user.fullName, user.avatarUrl, user.authProvider,
                user.isActive, user.isVerified, user.createdAt, user.updatedAt);
    }
}
