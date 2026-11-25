package com.sankalp.common;

// Thrown when a row does not exist (or belongs to another user) -> HTTP 404
public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) {
        super(message);
    }
}
