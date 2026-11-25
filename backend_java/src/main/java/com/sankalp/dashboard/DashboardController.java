package com.sankalp.dashboard;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.common.ApiResponse;
import com.sankalp.dashboard.DashboardDtos.DashboardSummary;

// One endpoint returns everything the dashboard page needs, so the page makes a single request.
@RestController
@RequestMapping("/api/v1/dashboard")
public class DashboardController {

    private final DashboardService service;

    public DashboardController(DashboardService service) {
        this.service = service;
    }

    @GetMapping("/summary")
    public ApiResponse<DashboardSummary> summary(@RequestAttribute("userId") String userId,
            @RequestParam(defaultValue = "30") int days) {
        return ApiResponse.ok(service.summary(userId, days));
    }
}
