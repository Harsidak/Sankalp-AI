package com.sankalp.tags;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.sankalp.common.ConflictException;
import com.sankalp.common.NotFoundException;
import com.sankalp.tags.TagDtos.TagCreate;
import com.sankalp.tags.TagDtos.TagRead;
import com.sankalp.tags.TagDtos.TagUpdate;
import com.sankalp.tags.TagDtos.TagWithCount;

// All the tag rules live here. @Transactional = one database transaction per method call
// (commit if it finishes, roll back if it throws).
@Service
@Transactional
public class TagService {

    private final TagRepository tags;

    public TagService(TagRepository tags) {
        this.tags = tags;
    }

    public List<TagWithCount> list(String userId, boolean withCounts) {
        if (withCounts) {
            return tags.findWithCounts(userId).stream()
                    .map(r -> new TagWithCount((String) r[0], (String) r[1], (String) r[2], ((Number) r[3]).longValue()))
                    .toList();
        }
        return tags.findByUserIdOrderByNameAsc(userId).stream()
                .map(t -> new TagWithCount(t.id, t.name, t.color, 0))
                .toList();
    }

    public TagRead create(String userId, TagCreate data) {
        String name = data.name().trim().toLowerCase();
        if (tags.findByUserIdAndName(userId, name).isPresent()) {
            throw new ConflictException("You already have a tag named '" + name + "'");
        }
        Tag tag = new Tag();
        tag.userId = userId;
        tag.name = name;
        if (data.color() != null) {
            tag.color = data.color();
        }
        tags.save(tag);
        return toRead(tag);
    }

    public TagRead update(String userId, String tagId, TagUpdate data) {
        Tag tag = getOwned(userId, tagId);
        if (data.name() != null) {
            String name = data.name().trim().toLowerCase();
            if (!name.equals(tag.name) && tags.findByUserIdAndName(userId, name).isPresent()) {
                throw new ConflictException("You already have a tag named '" + name + "'");
            }
            tag.name = name;
        }
        if (data.color() != null) {
            tag.color = data.color();
        }
        return toRead(tag); // no save() needed: changes to a loaded entity are written when the transaction ends
    }

    // The database's ON DELETE CASCADE removes the entry_tags rows; the journal entries stay.
    public void delete(String userId, String tagId) {
        tags.delete(getOwned(userId, tagId));
    }

    // "Owned" = belongs to this user. Someone else's tag looks exactly like a missing one.
    private Tag getOwned(String userId, String tagId) {
        return tags.findByIdAndUserId(tagId, userId)
                .orElseThrow(() -> new NotFoundException("Tag not found"));
    }

    private TagRead toRead(Tag tag) {
        return new TagRead(tag.id, tag.name, tag.color);
    }
}
