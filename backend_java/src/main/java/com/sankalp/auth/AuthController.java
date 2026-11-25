package com.sankalp.auth;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.auth.AuthDtos.AuthUserResponse;
import com.sankalp.auth.AuthDtos.LoginRequest;
import com.sankalp.auth.AuthDtos.RefreshTokenRequest;
import com.sankalp.auth.AuthDtos.RegisterRequest;
import com.sankalp.auth.AuthDtos.TokenResponse;
import com.sankalp.common.ApiResponse;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService service;

    public AuthController(AuthService service) {
        this.service = service;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<TokenResponse> register(@Valid @RequestBody RegisterRequest body) {
        return ApiResponse.ok(service.register(body), "Account created successfully");
    }

    @PostMapping("/login")
    public ApiResponse<TokenResponse> login(@Valid @RequestBody LoginRequest body) {
        return ApiResponse.ok(service.login(body), "Login successful");
    }

    @PostMapping("/refresh")
    public ApiResponse<TokenResponse> refresh(@Valid @RequestBody RefreshTokenRequest body) {
        return ApiResponse.ok(service.refresh(body), "Token refreshed");
    }

    @GetMapping("/me")
    public ApiResponse<AuthUserResponse> me(@RequestAttribute("userId") String userId) {
        return ApiResponse.ok(service.me(userId));
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(@Valid @RequestBody RefreshTokenRequest body) {
        service.logout(body);
        return ApiResponse.ok(null, "Logged out successfully");
    }
}
