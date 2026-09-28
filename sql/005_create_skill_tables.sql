USE recruit_insight;

CREATE TABLE IF NOT EXISTS skill (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    name VARCHAR(100) NOT NULL COMMENT '规范化技能名称',
    PRIMARY KEY (id),
    UNIQUE KEY uk_skill_name (name)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '技能字典';

CREATE TABLE IF NOT EXISTS job_skill (
    job_id BIGINT UNSIGNED NOT NULL COMMENT '岗位 ID',
    skill_id BIGINT UNSIGNED NOT NULL COMMENT '技能 ID',
    PRIMARY KEY (job_id, skill_id),
    KEY idx_job_skill_skill_id (skill_id),
    CONSTRAINT fk_job_skill_job
        FOREIGN KEY (job_id) REFERENCES job (id) ON DELETE CASCADE,
    CONSTRAINT fk_job_skill_skill
        FOREIGN KEY (skill_id) REFERENCES skill (id)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '岗位与技能多对多关系';
