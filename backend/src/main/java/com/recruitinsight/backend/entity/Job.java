package com.recruitinsight.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("job")
public class Job {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String sourceId;

    private String title;

    private String company;

    private String city;

    private String category;

    private String education;

    private Integer salaryMin;

    private Integer salaryMax;

    private Integer salaryMonths;

    private String description;

    private LocalDate publishDate;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
