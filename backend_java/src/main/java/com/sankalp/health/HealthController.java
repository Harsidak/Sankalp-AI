package com.sankalp.health;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

// Open in a browser or run:  curl http://localhost:8000/api/v1/health
@RestController
@RequestMapping("/api/v1")
public class HealthController {

    private final HealthService service;

    public HealthController(HealthService service) {
        this.service = service;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        boolean up = service.databaseIsUp();
        return Map.of(
                "status", up ? "healthy" : "degraded",
                "version", "1.0.0",
                "database", up ? "connected" : "disconnected");
    }
}
