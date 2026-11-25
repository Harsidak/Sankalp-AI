package com.sankalp.common;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

// One place that turns exceptions into the same JSON error shape the React app expects:
// { success: false, error: { code, message } }
@RestControllerAdvice
public class ErrorHandler {

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<?> notFound(NotFoundException e) {
        return body(HttpStatus.NOT_FOUND, "NOT_FOUND", e.getMessage());
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<?> conflict(ConflictException e) {
        return body(HttpStatus.CONFLICT, "CONFLICT", e.getMessage());
    }

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<?> unauthenticated(AuthenticationException e) {
        return body(HttpStatus.UNAUTHORIZED, "AUTHENTICATION_ERROR", e.getMessage());
    }

    // A request body broke a rule such as @Min(1) or @NotBlank
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<?> invalid(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().get(0).getField() + ": "
                + e.getBindingResult().getFieldErrors().get(0).getDefaultMessage();
        return body(HttpStatus.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message);
    }

    private ResponseEntity<?> body(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status)
                .body(Map.of("success", false, "error", Map.of("code", code, "message", message)));
    }
}
