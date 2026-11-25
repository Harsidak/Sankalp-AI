package com.sankalp.journal;

import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface JournalRepository extends JpaRepository<JournalEntry, String> {

    Optional<JournalEntry> findByIdAndUserId(String id, String userId);

    // pattern looks like %word% (just % means "everything"). Page = one slice of the results + the total count.
    @Query("""
            select e from JournalEntry e
            where e.userId = :userId and (e.title like :pattern or e.content like :pattern)
            """)
    Page<JournalEntry> search(@Param("userId") String userId, @Param("pattern") String pattern, Pageable pageable);

    // Same, but only entries that have at least one of the given tags.
    @Query("""
            select e from JournalEntry e
            where e.userId = :userId and (e.title like :pattern or e.content like :pattern)
              and e.id in (select x.id from JournalEntry x join x.tags t where t.id in :tagIds)
            """)
    Page<JournalEntry> searchWithTags(@Param("userId") String userId, @Param("pattern") String pattern,
            @Param("tagIds") List<String> tagIds, Pageable pageable);
}
