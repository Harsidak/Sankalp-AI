package com.sankalp.insights;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sankalp.common.ApiResponse;
import com.sankalp.insights.InsightsDtos.InsightsSummary;

@RestController
@RequestMapping("/api/v1/insights")
public class InsightsController {

    private final InsightsService service;

    public InsightsController(InsightsService service) {
        this.service = service;
    }

    @GetMapping("/summary")
    public ApiResponse<InsightsSummary> summary(@RequestAttribute("userId") String userId,
            @RequestParam(defaultValue = "30") int days) {
        return ApiResponse.ok(service.summary(userId, days));
    }
}
