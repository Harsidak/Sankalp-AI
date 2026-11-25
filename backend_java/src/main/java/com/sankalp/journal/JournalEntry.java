package com.sankalp.journal;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import com.sankalp.tags.Tag;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.Table;

// One row of `journal_entries`.
// An entry has many tags and a tag is on many entries (many-to-many).
// The join table `entry_tags` (entry_id, tag_id) connects them; JPA fills it for us.
@Entity
@Table(name = "journal_entries")
public class JournalEntry {

    @Id
    @Column(length = 36)
    public String id = UUID.randomUUID().toString();

    public String userId;
    public String title = "Untitled";
    public String content;
    public Instant createdAt = Instant.now();
    public Instant updatedAt = Instant.now();

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(name = "entry_tags",
            joinColumns = @JoinColumn(name = "entry_id"),
            inverseJoinColumns = @JoinColumn(name = "tag_id"))
    public Set<Tag> tags = new HashSet<>();
}
