package com.recruitinsight.backend.dto.statistics;

import lombok.Data;

@Data
public class OverviewStatistics {

    private Long totalJobs;
    private Long totalCompanies;
    private Long totalCities;
    private Long totalSkills;
    private Long salaryKnownJobs;
    private Long salaryUnknownJobs;
}
