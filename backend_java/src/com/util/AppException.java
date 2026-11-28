package com.util;

// Our own exception for mistakes the user makes (for example "no habit with that number").
public class AppException extends Exception {
    public AppException(String message) {
        super(message);
    }
}
