package com.recruitinsight.backend.service;

import com.recruitinsight.backend.dto.statistics.CategoryStatistics;
import com.recruitinsight.backend.dto.statistics.CityStatistics;
import com.recruitinsight.backend.dto.statistics.OverviewStatistics;
import com.recruitinsight.backend.dto.statistics.SalaryStatistics;
import com.recruitinsight.backend.dto.statistics.SkillStatistics;

import java.util.List;

public interface StatisticsService {

    OverviewStatistics getOverview();

    List<SkillStatistics> getTopSkills(int limit, String category);

    List<CityStatistics> getCityStatistics();

    List<CategoryStatistics> getCategoryStatistics();

    List<SalaryStatistics> getSalaryStatistics();
}
