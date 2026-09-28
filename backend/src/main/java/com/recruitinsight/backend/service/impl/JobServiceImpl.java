package com.recruitinsight.backend.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.recruitinsight.backend.entity.Job;
import com.recruitinsight.backend.mapper.JobMapper;
import com.recruitinsight.backend.service.JobService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class JobServiceImpl extends ServiceImpl<JobMapper, Job> implements JobService {

    @Override
    public Page<Job> searchJobs(
            int page,
            int size,
            String keyword,
            String city,
            String category,
            String company
    ) {
        String normalizedKeyword = normalize(keyword);
        String normalizedCity = normalize(city);
        String normalizedCategory = normalize(category);
        String normalizedCompany = normalize(company);

        LambdaQueryWrapper<Job> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper
                .like(StringUtils.hasText(normalizedKeyword), Job::getTitle, normalizedKeyword)
                .eq(StringUtils.hasText(normalizedCity), Job::getCity, normalizedCity)
                .eq(StringUtils.hasText(normalizedCategory), Job::getCategory, normalizedCategory)
                .like(StringUtils.hasText(normalizedCompany), Job::getCompany, normalizedCompany)
                .orderByDesc(Job::getPublishDate)
                .orderByDesc(Job::getId);

        return page(new Page<>(page, size), queryWrapper);
    }

    private String normalize(String value) {
        return value == null ? null : value.trim();
    }
}
