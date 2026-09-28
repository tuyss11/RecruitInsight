package com.recruitinsight.backend.mapper;

import com.recruitinsight.backend.dto.statistics.CategoryStatistics;
import com.recruitinsight.backend.dto.statistics.CityStatistics;
import com.recruitinsight.backend.dto.statistics.OverviewStatistics;
import com.recruitinsight.backend.dto.statistics.SalaryStatistics;
import com.recruitinsight.backend.dto.statistics.SkillStatistics;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface StatisticsMapper {

    OverviewStatistics selectOverview();

    List<SkillStatistics> selectTopSkills(
            @Param("category") String category,
            @Param("limit") int limit
    );

    List<CityStatistics> selectCityStatistics();

    List<CategoryStatistics> selectCategoryStatistics();

    List<SalaryStatistics> selectSalaryStatistics();
}
