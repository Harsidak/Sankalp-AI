package com.sankalp.tags;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

// Spring writes the SQL for these method names automatically
// (findByUserIdOrderByNameAsc -> select * from tags where user_id = ? order by name asc).
public interface TagRepository extends JpaRepository<Tag, String> {

    List<Tag> findByUserIdOrderByNameAsc(String userId);

    Optional<Tag> findByIdAndUserId(String id, String userId);

    Optional<Tag> findByUserIdAndName(String userId, String name);

    List<Tag> findByUserIdAndIdIn(String userId, List<String> ids);

    // LEFT JOIN keeps tags that no entry uses yet (count = 0). An inner join would drop them.
    @Query(nativeQuery = true, value = """
            select t.id, t.name, t.color, count(et.entry_id)
            from tags t
            left join entry_tags et on et.tag_id = t.id
            where t.user_id = :userId
            group by t.id, t.name, t.color
            order by count(et.entry_id) desc, t.name asc
            """)
    List<Object[]> findWithCounts(@Param("userId") String userId);
}
