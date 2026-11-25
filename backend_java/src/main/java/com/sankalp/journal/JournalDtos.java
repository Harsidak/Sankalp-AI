package com.sankalp.journal;

import java.time.Instant;
import java.util.List;

import com.sankalp.tags.TagDtos.TagRead;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class JournalDtos {

    public record JournalCreate(
            @Size(max = 255) String title,
            @NotBlank String content,
            List<String> tagIds) {
    }

    // Any field may be null = "leave unchanged". tagIds, when sent, replaces ALL tags of the entry.
    public record JournalUpdate(
            @Size(max = 255) String title,
            String content,
            List<String> tagIds) {
    }

    public record JournalRead(
            String id, String title, String content, List<TagRead> tags, Instant createdAt, Instant updatedAt) {
    }
}
