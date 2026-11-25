package com.sankalp.habits;

import java.util.List;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.common.ApiResponse;
import com.sankalp.habits.HabitDtos.HabitCreate;
import com.sankalp.habits.HabitDtos.HabitLogResult;
import com.sankalp.habits.HabitDtos.HabitLogToggle;
import com.sankalp.habits.HabitDtos.HabitRead;
import com.sankalp.habits.HabitDtos.HabitUpdate;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/habits")
public class HabitController {

    private final HabitService service;

    public HabitController(HabitService service) {
        this.service = service;
    }

    @GetMapping
    public ApiResponse<List<HabitRead>> list(@RequestAttribute("userId") String userId,
            @RequestParam(name = "include_archived", defaultValue = "false") boolean includeArchived) {
        return ApiResponse.ok(service.list(userId, includeArchived));
    }

    @GetMapping("/{id}")
    public ApiResponse<HabitRead> get(@RequestAttribute("userId") String userId, @PathVariable String id) {
        return ApiResponse.ok(service.get(userId, id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<HabitRead> create(@RequestAttribute("userId") String userId,
            @Valid @RequestBody HabitCreate body) {
        return ApiResponse.ok(service.create(userId, body));
    }

    @PatchMapping("/{id}")
    public ApiResponse<HabitRead> update(@RequestAttribute("userId") String userId, @PathVariable String id,
            @Valid @RequestBody HabitUpdate body) {
        return ApiResponse.ok(service.update(userId, id, body));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, Boolean>> delete(@RequestAttribute("userId") String userId,
            @PathVariable String id) {
        service.delete(userId, id);
        return ApiResponse.ok(Map.of("deleted", true), "Habit deleted");
    }

    // Tick / untick a day. The React checkbox calls only this.
    @PostMapping("/{id}/log")
    public ApiResponse<HabitLogResult> toggle(@RequestAttribute("userId") String userId, @PathVariable String id,
            @RequestBody(required = false) HabitLogToggle body) {
        return ApiResponse.ok(service.toggle(userId, id, body == null ? null : body.completedDate()));
    }
}
