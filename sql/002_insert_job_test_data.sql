USE recruit_insight;

INSERT INTO job (
    id,
    title,
    company,
    city,
    category,
    salary_min,
    salary_max,
    description,
    publish_date
) VALUES
    (1, 'Java后端开发实习生', '示例科技有限公司', '上海', '后端开发', 3000, 5000,
     '参与示例业务接口开发与单元测试。仅用于项目功能测试。', '2026-09-20'),
    (2, '数据分析实习生', '测试数据有限公司', '北京', '数据分析', 2500, 4000,
     '使用 SQL 和表格工具完成模拟数据分析。仅用于项目功能测试。', '2026-09-21'),
    (3, 'Python数据开发实习生', '演示软件有限公司', '杭州', '数据开发', 3500, 5500,
     '参与模拟数据采集与处理脚本开发。仅用于项目功能测试。', '2026-09-22'),
    (4, '测试开发实习生', '样例网络有限公司', '深圳', '测试', 2800, 4500,
     '参与接口自动化测试用例编写。仅用于项目功能测试。', '2026-09-23')
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    company = VALUES(company),
    city = VALUES(city),
    category = VALUES(category),
    salary_min = VALUES(salary_min),
    salary_max = VALUES(salary_max),
    description = VALUES(description),
    publish_date = VALUES(publish_date);

