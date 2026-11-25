package com.sankalp.health;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class HealthService {

    private final JdbcTemplate jdbc;

    public HealthService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    // Can we run a trivial query? If the database is down this throws, which is exactly what we want to report.
    public boolean databaseIsUp() {
        try {
            jdbc.queryForObject("select 1", Integer.class);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
