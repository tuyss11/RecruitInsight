package com.recruitinsight.backend.dto.statistics;

import lombok.Data;

@Data
public class SalaryStatistics {

    private String category;
    private Long jobCount;
    private Long averageSalaryMin;
    private Long averageSalaryMax;
    private Long averageSalaryMid;
}
