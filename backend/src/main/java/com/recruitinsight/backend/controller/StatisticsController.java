package com.recruitinsight.backend.controller;

import com.recruitinsight.backend.dto.statistics.CategoryStatistics;
import com.recruitinsight.backend.dto.statistics.CityStatistics;
import com.recruitinsight.backend.dto.statistics.OverviewStatistics;
import com.recruitinsight.backend.dto.statistics.SalaryStatistics;
import com.recruitinsight.backend.dto.statistics.SkillStatistics;
import com.recruitinsight.backend.service.StatisticsService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api/statistics")
public class StatisticsController {

    private final StatisticsService statisticsService;

    public StatisticsController(StatisticsService statisticsService) {
        this.statisticsService = statisticsService;
    }

    @GetMapping("/overview")
    public OverviewStatistics overview() {
        return statisticsService.getOverview();
    }

    @GetMapping("/skills")
    public List<SkillStatistics> skills(
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(required = false) String category
    ) {
        if (limit < 1 || limit > 50) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "limit 必须在 1 到 50 之间"
            );
        }
        return statisticsService.getTopSkills(limit, category);
    }

    @GetMapping("/cities")
    public List<CityStatistics> cities() {
        return statisticsService.getCityStatistics();
    }

    @GetMapping("/categories")
    public List<CategoryStatistics> categories() {
        return statisticsService.getCategoryStatistics();
    }

    @GetMapping("/salary")
    public List<SalaryStatistics> salary() {
        return statisticsService.getSalaryStatistics();
    }
}
