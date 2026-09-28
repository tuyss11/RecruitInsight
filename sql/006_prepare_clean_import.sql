USE recruit_insight;

-- 使用事务型 DELETE 保留表结构和自增状态，并按外键依赖顺序清理模拟数据。
START TRANSACTION;
DELETE FROM job_skill;
DELETE FROM skill;
DELETE FROM job;
COMMIT;
