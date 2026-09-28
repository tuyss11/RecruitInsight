package com.recruitinsight.backend.service.impl;

import com.recruitinsight.backend.dto.statistics.CategoryStatistics;
import com.recruitinsight.backend.dto.statistics.CityStatistics;
import com.recruitinsight.backend.dto.statistics.OverviewStatistics;
import com.recruitinsight.backend.dto.statistics.SalaryStatistics;
import com.recruitinsight.backend.dto.statistics.SkillStatistics;
import com.recruitinsight.backend.mapper.StatisticsMapper;
import com.recruitinsight.backend.service.StatisticsService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@Service
public class StatisticsServiceImpl implements StatisticsService {

    private static final int PERCENTAGE_SCALE = 2;
    private static final BigDecimal ONE_HUNDRED = BigDecimal.valueOf(100);

    private final StatisticsMapper statisticsMapper;

    public StatisticsServiceImpl(StatisticsMapper statisticsMapper) {
        this.statisticsMapper = statisticsMapper;
    }

    @Override
    public OverviewStatistics getOverview() {
        return statisticsMapper.selectOverview();
    }

    @Override
    public List<SkillStatistics> getTopSkills(int limit, String category) {
        String normalizedCategory = StringUtils.hasText(category) ? category.trim() : null;
        return statisticsMapper.selectTopSkills(normalizedCategory, limit);
    }

    @Override
    public List<CityStatistics> getCityStatistics() {
        return statisticsMapper.selectCityStatistics();
    }

    @Override
    public List<CategoryStatistics> getCategoryStatistics() {
        List<CategoryStatistics> statistics = statisticsMapper.selectCategoryStatistics();
        long totalJobs = statistics.stream()
                .mapToLong(item -> item.getJobCount() == null ? 0 : item.getJobCount())
                .sum();

        for (CategoryStatistics item : statistics) {
            item.setPercentage(calculatePercentage(item.getJobCount(), totalJobs));
        }
        return statistics;
    }

    @Override
    public List<SalaryStatistics> getSalaryStatistics() {
        return statisticsMapper.selectSalaryStatistics();
    }

    private BigDecimal calculatePercentage(Long count, long total) {
        if (count == null || total == 0) {
            return BigDecimal.ZERO.setScale(PERCENTAGE_SCALE, RoundingMode.HALF_UP);
        }
        return BigDecimal.valueOf(count)
                .multiply(ONE_HUNDRED)
                .divide(BigDecimal.valueOf(total), PERCENTAGE_SCALE, RoundingMode.HALF_UP);
    }
}
