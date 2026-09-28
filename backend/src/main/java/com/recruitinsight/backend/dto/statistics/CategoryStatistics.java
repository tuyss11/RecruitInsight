package com.recruitinsight.backend.dto.statistics;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class CategoryStatistics {

    private String category;
    private Long jobCount;
    private BigDecimal percentage;
}
