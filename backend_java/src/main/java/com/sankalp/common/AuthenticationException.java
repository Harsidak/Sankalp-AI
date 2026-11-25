package com.sankalp.common;

// Thrown when credentials or tokens are invalid -> HTTP 401, same error code
// as the Python backend's AuthenticationError.
public class AuthenticationException extends RuntimeException {
    public AuthenticationException(String message) {
        super(message);
    }
}
