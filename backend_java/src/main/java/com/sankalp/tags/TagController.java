package com.sankalp.tags;

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
import com.sankalp.tags.TagDtos.TagCreate;
import com.sankalp.tags.TagDtos.TagRead;
import com.sankalp.tags.TagDtos.TagUpdate;
import com.sankalp.tags.TagDtos.TagWithCount;

import jakarta.validation.Valid;

// The controller only handles HTTP: read the request, call the service, wrap the answer.
// "userId" is put on the request by the auth module's JwtFilter after it checks the token.
@RestController
@RequestMapping("/api/v1/tags")
public class TagController {

    private final TagService service;

    public TagController(TagService service) {
        this.service = service;
    }

    @GetMapping
    public ApiResponse<List<TagWithCount>> list(
            @RequestAttribute("userId") String userId,
            @RequestParam(name = "with_counts", defaultValue = "true") boolean withCounts) {
        return ApiResponse.ok(service.list(userId, withCounts));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<TagRead> create(@RequestAttribute("userId") String userId, @Valid @RequestBody TagCreate body) {
        return ApiResponse.ok(service.create(userId, body));
    }

    @PatchMapping("/{id}")
    public ApiResponse<TagRead> update(@RequestAttribute("userId") String userId, @PathVariable String id,
            @Valid @RequestBody TagUpdate body) {
        return ApiResponse.ok(service.update(userId, id, body));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, Boolean>> delete(@RequestAttribute("userId") String userId, @PathVariable String id) {
        service.delete(userId, id);
        return ApiResponse.ok(Map.of("deleted", true), "Tag deleted");
    }
}
