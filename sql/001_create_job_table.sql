USE recruit_insight;

CREATE TABLE IF NOT EXISTS job (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    title VARCHAR(100) NOT NULL COMMENT '岗位名称',
    company VARCHAR(150) NOT NULL COMMENT '公司名称',
    city VARCHAR(50) NOT NULL COMMENT '城市',
    category VARCHAR(50) NOT NULL COMMENT '岗位类别',
    salary_min INT UNSIGNED DEFAULT NULL COMMENT '最低月薪（元）',
    salary_max INT UNSIGNED DEFAULT NULL COMMENT '最高月薪（元）',
    description TEXT COMMENT '岗位描述',
    publish_date DATE DEFAULT NULL COMMENT '发布日期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    CONSTRAINT chk_job_salary_range
        CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '招聘岗位';

