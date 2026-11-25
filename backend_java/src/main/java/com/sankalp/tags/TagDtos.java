package com.sankalp.tags;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

// DTO = the shape of the JSON going in and out. Requests are validated, responses are plain.
public class TagDtos {

    static final String HEX = "^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$";

    public record TagCreate(
            @NotBlank @Size(max = 50) String name,
            @Pattern(regexp = HEX) String color) {
    }

    // Any field may be null = "leave unchanged"
    public record TagUpdate(
            @Size(min = 1, max = 50) String name,
            @Pattern(regexp = HEX) String color) {
    }

    public record TagRead(String id, String name, String color) {
    }

    public record TagWithCount(String id, String name, String color, long entryCount) {
    }
}
