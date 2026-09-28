package com.recruitinsight.backend.service.impl;

import com.recruitinsight.backend.cache.StatisticsCacheKeys;
import com.recruitinsight.backend.dto.statistics.CategoryStatistics;
import com.recruitinsight.backend.dto.statistics.CityStatistics;
import com.recruitinsight.backend.dto.statistics.OverviewStatistics;
import com.recruitinsight.backend.dto.statistics.SalaryStatistics;
import com.recruitinsight.backend.dto.statistics.SkillStatistics;
import com.recruitinsight.backend.mapper.StatisticsMapper;
import com.recruitinsight.backend.service.StatisticsService;
import org.springframework.cache.annotation.Cacheable;
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
    @Cacheable(
            cacheNames = StatisticsCacheKeys.CACHE_NAME,
            key = "'overview'",
            unless = "#result == null"
    )
    public OverviewStatistics getOverview() {
        return statisticsMapper.selectOverview();
    }

    @Override
    @Cacheable(
            cacheNames = StatisticsCacheKeys.CACHE_NAME,
            key = "T(com.recruitinsight.backend.cache.StatisticsCacheKeys).skills(#limit, #category)",
            unless = "#result == null || #result.isEmpty()"
    )
    public List<SkillStatistics> getTopSkills(int limit, String category) {
        String normalizedCategory = StringUtils.hasText(category) ? category.trim() : null;
        return statisticsMapper.selectTopSkills(normalizedCategory, limit);
    }

    @Override
    @Cacheable(
            cacheNames = StatisticsCacheKeys.CACHE_NAME,
            key = "'cities'",
            unless = "#result == null || #result.isEmpty()"
    )
    public List<CityStatistics> getCityStatistics() {
        return statisticsMapper.selectCityStatistics();
    }

    @Override
    @Cacheable(
            cacheNames = StatisticsCacheKeys.CACHE_NAME,
            key = "'categories'",
            unless = "#result == null || #result.isEmpty()"
    )
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
    @Cacheable(
            cacheNames = StatisticsCacheKeys.CACHE_NAME,
            key = "'salary'",
            unless = "#result == null || #result.isEmpty()"
    )
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
