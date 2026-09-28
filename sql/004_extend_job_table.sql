USE recruit_insight;

ALTER TABLE job
    ADD COLUMN source_id VARCHAR(64) NULL COMMENT '原始 CSV 记录 ID' AFTER id,
    ADD COLUMN education VARCHAR(50) NOT NULL DEFAULT '不限' COMMENT '学历要求' AFTER category,
    ADD COLUMN salary_months TINYINT UNSIGNED NULL COMMENT '一年发薪月数' AFTER salary_max,
    MODIFY COLUMN salary_min INT UNSIGNED NULL COMMENT '最低月薪（元）',
    MODIFY COLUMN salary_max INT UNSIGNED NULL COMMENT '最高月薪（元）',
    MODIFY COLUMN description TEXT NULL COMMENT '岗位描述',
    ADD UNIQUE INDEX uk_job_source_id (source_id);
