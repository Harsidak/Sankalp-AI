package com.sankalp.journal;

import java.util.List;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.common.ApiResponse;
import com.sankalp.journal.JournalDtos.JournalCreate;
import com.sankalp.journal.JournalDtos.JournalRead;
import com.sankalp.journal.JournalDtos.JournalUpdate;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/journal")
public class JournalController {

    private final JournalService service;

    public JournalController(JournalService service) {
        this.service = service;
    }

    // GET /journal?search=sad&tag_ids=a&tag_ids=b&page=1&page_size=20
    @GetMapping
    public ApiResponse.Page<JournalRead> list(@RequestAttribute("userId") String userId,
            @RequestParam(required = false) String search,
            @RequestParam(name = "tag_ids", required = false) List<String> tagIds,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize) {
        return service.list(userId, search, tagIds, page, pageSize);
    }

    @GetMapping("/{id}")
    public ApiResponse<JournalRead> get(@RequestAttribute("userId") String userId, @PathVariable String id) {
        return ApiResponse.ok(service.get(userId, id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<JournalRead> create(@RequestAttribute("userId") String userId,
            @Valid @RequestBody JournalCreate body) {
        return ApiResponse.ok(service.create(userId, body));
    }

    @PutMapping("/{id}")
    public ApiResponse<JournalRead> update(@RequestAttribute("userId") String userId, @PathVariable String id,
            @Valid @RequestBody JournalUpdate body) {
        return ApiResponse.ok(service.update(userId, id, body));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, Boolean>> delete(@RequestAttribute("userId") String userId,
            @PathVariable String id) {
        service.delete(userId, id);
        return ApiResponse.ok(Map.of("deleted", true), "Entry deleted");
    }
}
