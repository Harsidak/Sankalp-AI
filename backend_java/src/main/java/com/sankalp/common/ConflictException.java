package com.sankalp.common;

// Thrown when something already exists (e.g. duplicate tag name) -> HTTP 409
public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
