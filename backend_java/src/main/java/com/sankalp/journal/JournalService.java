package com.sankalp.journal;

import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.common.ApiResponse;
import com.sankalp.common.NotFoundException;
import com.sankalp.journal.JournalDtos.JournalCreate;
import com.sankalp.journal.JournalDtos.JournalRead;
import com.sankalp.journal.JournalDtos.JournalUpdate;
import com.sankalp.tags.Tag;
import com.sankalp.tags.TagDtos.TagRead;
import com.sankalp.tags.TagRepository;

@Service
@Transactional
public class JournalService {

    private final JournalRepository entries;
    private final TagRepository tags;

    public JournalService(JournalRepository entries, TagRepository tags) {
        this.entries = entries;
        this.tags = tags;
    }

    // Newest first. search and tagIds are optional filters and can be combined.
    public ApiResponse.Page<JournalRead> list(String userId, String search, List<String> tagIds, int page, int pageSize) {
        String pattern = (search == null || search.isBlank()) ? "%" : "%" + search.trim() + "%";
        PageRequest pageRequest = PageRequest.of(page - 1, pageSize, Sort.by("createdAt").descending());

        Page<JournalEntry> result = (tagIds == null || tagIds.isEmpty())
                ? entries.search(userId, pattern, pageRequest)
                : entries.searchWithTags(userId, pattern, tagIds, pageRequest);

        return new ApiResponse.Page<>(true, result.map(this::toRead).getContent(),
                result.getTotalElements(), page, pageSize, result.getTotalPages());
    }

    public JournalRead get(String userId, String entryId) {
        return toRead(getOwned(userId, entryId));
    }

    public JournalRead create(String userId, JournalCreate data) {
        JournalEntry entry = new JournalEntry();
        entry.userId = userId;
        if (data.title() != null && !data.title().isBlank()) {
            entry.title = data.title();
        }
        entry.content = data.content();
        entry.tags = findTags(userId, data.tagIds());
        entries.save(entry);
        return toRead(entry);
    }

    public JournalRead update(String userId, String entryId, JournalUpdate data) {
        JournalEntry entry = getOwned(userId, entryId);
        if (data.title() != null) {
            entry.title = data.title();
        }
        if (data.content() != null) {
            entry.content = data.content();
        }
        if (data.tagIds() != null) {
            entry.tags = findTags(userId, data.tagIds());
        }
        entry.updatedAt = Instant.now();
        return toRead(entry);
    }

    // The entry_tags rows go with it; the tags themselves stay.
    public void delete(String userId, String entryId) {
        entries.delete(getOwned(userId, entryId));
    }

    // Only this user's tags are accepted; unknown ids are ignored.
    private Set<Tag> findTags(String userId, List<String> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return new HashSet<>();
        }
        return new HashSet<>(tags.findByUserIdAndIdIn(userId, tagIds));
    }

    private JournalEntry getOwned(String userId, String entryId) {
        return entries.findByIdAndUserId(entryId, userId)
                .orElseThrow(() -> new NotFoundException("Journal entry not found"));
    }

    private JournalRead toRead(JournalEntry e) {
        List<TagRead> tagReads = e.tags.stream()
                .map(t -> new TagRead(t.id, t.name, t.color))
                .toList();
        return new JournalRead(e.id, e.title, e.content, tagReads, e.createdAt, e.updatedAt);
    }
}
