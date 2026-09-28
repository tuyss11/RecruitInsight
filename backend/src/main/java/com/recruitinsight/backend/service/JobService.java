package com.recruitinsight.backend.service;

import com.baomidou.mybatisplus.spring.service.IService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruitinsight.backend.entity.Job;

public interface JobService extends IService<Job> {

    Page<Job> searchJobs(
            int page,
            int size,
            String keyword,
            String city,
            String category,
            String company
    );
}
