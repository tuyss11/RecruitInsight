<script setup>
import CategoriesChart from '../components/CategoriesChart.vue'
import CitiesChart from '../components/CitiesChart.vue'
import JobTable from '../components/JobTable.vue'
import OverviewCards from '../components/OverviewCards.vue'
import SalaryChart from '../components/SalaryChart.vue'
import SkillsChart from '../components/SkillsChart.vue'
</script>

<template>
  <div class="dashboard-shell">
    <header class="site-header">
      <div class="brand-mark" aria-hidden="true">RI</div>
      <div class="brand-copy">
        <p class="brand-name">RecruitInsight</p>
        <p>招聘数据分析平台</p>
      </div>
      <span class="header-status"><i></i> API Connected</span>
    </header>

    <main>
      <section class="hero-section">
        <div>
          <p class="eyebrow">RECRUITMENT DATA ANALYSIS DASHBOARD</p>
          <h1>看清岗位、技能与薪资的结构</h1>
          <p class="hero-description">
            从清洗后的岗位数据出发，以统一口径呈现技能需求、城市分布、岗位类别与月薪区间。
          </p>
        </div>
        <aside class="simulation-notice">
          <span>演示数据说明</span>
          <strong>当前数据为项目模拟数据，仅用于功能演示。</strong>
        </aside>
      </section>

      <OverviewCards />

      <section class="chart-grid" aria-label="招聘统计图表">
        <SkillsChart />
        <CitiesChart />
        <CategoriesChart />
        <SalaryChart />
      </section>

      <JobTable />
    </main>

    <footer class="site-footer">
      <span>RecruitInsight</span>
      <span>Vue 3 · ECharts · Spring Boot</span>
    </footer>
  </div>
</template>
