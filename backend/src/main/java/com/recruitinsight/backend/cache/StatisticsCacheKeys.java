package com.recruitinsight.backend.cache;

import org.springframework.util.StringUtils;

public final class StatisticsCacheKeys {

    public static final String CACHE_NAME = "statistics";

    private StatisticsCacheKeys() {
    }

    public static String skills(int limit, String category) {
        String normalizedCategory = StringUtils.hasText(category) ? category.trim() : "all";
        return "skills:" + normalizedCategory + ":" + limit;
    }
}
