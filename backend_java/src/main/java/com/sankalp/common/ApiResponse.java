package com.sankalp.common;

import java.util.List;

// Every endpoint returns this same envelope: { success, data, message }.
// A record is a class with only fields + a constructor + getters, written in one line.
public record ApiResponse<T>(boolean success, T data, String message) {

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(true, data, null);
    }

    public static <T> ApiResponse<T> ok(T data, String message) {
        return new ApiResponse<>(true, data, message);
    }

    // Same envelope for lists that have pages: total, page, page_size, total_pages sit next to data.
    public record Page<T>(boolean success, List<T> data, long total, int page, int pageSize, int totalPages) {
    }
}
