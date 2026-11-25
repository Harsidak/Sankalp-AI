package com.sankalp.auth;

import java.io.IOException;
import java.util.Map;
import java.util.Set;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sankalp.users.User;
import com.sankalp.users.UserRepository;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

// The contract every module relies on: a valid access token becomes the
// request attribute "userId"; anything else gets a 401 in the API's error shape.
@Component
public class JwtFilter extends OncePerRequestFilter {

    private static final Set<String> OPEN_PATHS = Set.of(
            "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh", "/api/v1/health");

    private final JwtService jwt;
    private final UserRepository users;
    private final ObjectMapper json;

    public JwtFilter(JwtService jwt, UserRepository users, ObjectMapper json) {
        this.jwt = jwt;
        this.users = users;
        this.json = json;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return "OPTIONS".equalsIgnoreCase(request.getMethod()) || OPEN_PATHS.contains(request.getRequestURI());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String header = request.getHeader("Authorization");
        if (header == null || header.isBlank()) {
            fail(response, "Authorization header is required");
            return;
        }

        String[] parts = header.trim().split("\\s+");
        if (parts.length != 2 || !"bearer".equalsIgnoreCase(parts[0])) {
            fail(response, "Invalid authorization header format. Use: Bearer <token>");
            return;
        }

        Claims claims;
        try {
            claims = jwt.parse(parts[1]);
        } catch (JwtException | IllegalArgumentException e) {
            fail(response, "Invalid or expired access token");
            return;
        }
        if (!"access".equals(jwt.typeOf(claims))) {
            fail(response, "Invalid or expired access token");
            return;
        }

        String userId = claims.getSubject();
        if (userId == null || userId.isBlank()) {
            fail(response, "Invalid token payload");
            return;
        }
        User user = users.findById(userId).orElse(null);
        if (user == null) {
            fail(response, "User not found");
            return;
        }
        if (!user.isActive) {
            fail(response, "Account is deactivated");
            return;
        }

        request.setAttribute("userId", userId);
        chain.doFilter(request, response);
    }

    // Filters run before @RestControllerAdvice, so the envelope is written here.
    private void fail(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(json.writeValueAsString(Map.of(
                "success", false,
                "error", Map.of("code", "AUTHENTICATION_ERROR", "message", message))));
    }
}
