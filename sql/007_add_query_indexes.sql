-- Run against the explicitly selected RecruitInsight database.
-- This file intentionally has no USE statement so the same verified schema
-- change can be measured on recruit_insight_perf and later applied to
-- recruit_insight without embedding environment-specific database selection.

-- A/D: equality filters on city + category; A also reads newest rows first.
CREATE INDEX idx_job_city_category_publish
    ON job (city, category, publish_date DESC, id DESC);

-- B: city-only pagination cannot preserve publish order through the category
-- column of the previous index. This index also gives G a city-leading index.
CREATE INDEX idx_job_city_publish
    ON job (city, publish_date DESC, id DESC);

-- C/F: category-only pagination and the category-filtered skill aggregation.
-- salary_min/salary_max are trailing covering columns for H; they do not
-- disturb the equality + publish-order prefix used by category pagination.
CREATE INDEX idx_job_category_publish
    ON job (category, publish_date DESC, id DESC, salary_min, salary_max);
