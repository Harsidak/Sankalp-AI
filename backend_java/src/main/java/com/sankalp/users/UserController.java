package com.sankalp.users;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.common.ApiResponse;
import com.sankalp.users.UserDtos.ChangePasswordRequest;
import com.sankalp.users.UserDtos.UserRead;
import com.sankalp.users.UserDtos.UserUpdate;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService service;

    public UserController(UserService service) {
        this.service = service;
    }

    @GetMapping("/me")
    public ApiResponse<UserRead> me(@RequestAttribute("userId") String userId) {
        return ApiResponse.ok(service.profile(userId));
    }

    @PutMapping("/me")
    public ApiResponse<UserRead> update(@RequestAttribute("userId") String userId,
            @Valid @RequestBody UserUpdate body) {
        return ApiResponse.ok(service.updateProfile(userId, body), "Profile updated");
    }

    @PutMapping("/me/password")
    public ApiResponse<Void> changePassword(@RequestAttribute("userId") String userId,
            @Valid @RequestBody ChangePasswordRequest body) {
        service.changePassword(userId, body);
        return ApiResponse.ok(null, "Password changed successfully");
    }
}
