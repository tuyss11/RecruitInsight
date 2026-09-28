package com.recruitinsight.backend.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.recruitinsight.backend.entity.Job;
import com.recruitinsight.backend.mapper.JobMapper;
import com.recruitinsight.backend.service.JobService;
import org.springframework.stereotype.Service;

@Service
public class JobServiceImpl extends ServiceImpl<JobMapper, Job> implements JobService {
}
