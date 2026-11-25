package com.sankalp.checkins;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.checkins.CheckInDtos.CheckInCreate;
import com.sankalp.checkins.CheckInDtos.CheckInRead;
import com.sankalp.checkins.CheckInDtos.CheckInUpdate;
import com.sankalp.checkins.CheckInDtos.StreakRead;
import com.sankalp.common.ApiResponse;

import jakarta.validation.Valid;

// The user id comes from JwtFilter, never from the request body, so one user
// cannot read or write another user's check-ins.
@RestController
@RequestMapping("/api/v1/checkins")
public class CheckInController {

    private final CheckInService service;

    public CheckInController(CheckInService service) {
        this.service = service;
    }

    // GET /checkins?start=2026-01-01&end=2026-01-31, or /checkins?days=30
    @GetMapping
    public ApiResponse<List<CheckInRead>> list(@RequestAttribute("userId") String userId,
            @RequestParam(required = false) LocalDate start,
            @RequestParam(required = false) LocalDate end,
            @RequestParam(defaultValue = "30") int days) {
        return ApiResponse.ok(service.list(userId, start, end, days));
    }

    @GetMapping("/today")
    public ApiResponse<CheckInRead> today(@RequestAttribute("userId") String userId) {
        return ApiResponse.ok(service.today(userId));
    }

    @GetMapping("/streak")
    public ApiResponse<StreakRead> streak(@RequestAttribute("userId") String userId) {
        return ApiResponse.ok(service.streak(userId));
    }

    // No @ResponseStatus(CREATED): the Python endpoint answers 200, and the
    // React client treats a re-rating of today as a normal save either way.
    @PostMapping
    public ApiResponse<CheckInRead> create(@RequestAttribute("userId") String userId,
            @Valid @RequestBody CheckInCreate body) {
        return ApiResponse.ok(service.createOrUpdate(userId, body));
    }

    @PatchMapping("/{id}")
    public ApiResponse<CheckInRead> update(@RequestAttribute("userId") String userId, @PathVariable String id,
            @Valid @RequestBody CheckInUpdate body) {
        return ApiResponse.ok(service.update(userId, id, body));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, Boolean>> delete(@RequestAttribute("userId") String userId,
            @PathVariable String id) {
        service.delete(userId, id);
        return ApiResponse.ok(Map.of("deleted", true), "Check-in deleted");
    }
}
