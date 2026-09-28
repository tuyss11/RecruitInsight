<script setup>
import { onMounted, ref } from 'vue'
import { getOverview } from '../api/statistics'

const overview = ref(null)
const loading = ref(true)
const error = ref('')
const cards = [
  { key: 'totalJobs', label: '岗位总数', hint: 'Jobs' },
  { key: 'totalCompanies', label: '公司数量', hint: 'Companies' },
  { key: 'totalCities', label: '城市数量', hint: 'Cities' },
  { key: 'totalSkills', label: '技能数量', hint: 'Skills' },
  { key: 'salaryKnownJobs', label: '有效薪资岗位', hint: 'Salary known' },
  { key: 'salaryUnknownJobs', label: '未知薪资岗位', hint: 'Salary unknown' },
]

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    overview.value = await getOverview()
  } catch (requestError) {
    error.value = '概览数据加载失败'
    console.error('Failed to load overview statistics', requestError)
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<template>
  <section aria-labelledby="overview-heading">
    <div class="section-heading compact-heading">
      <div>
        <p class="eyebrow">OVERVIEW</p>
        <h2 id="overview-heading">数据概览</h2>
      </div>
      <span class="data-source-label">实时 API</span>
    </div>
    <div v-if="loading" class="overview-state">概览数据加载中...</div>
    <div v-else-if="error" class="overview-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadOverview">重新加载</button>
    </div>
    <div v-else-if="overview" class="overview-grid">
      <article v-for="card in cards" :key="card.key" class="overview-card">
        <div class="card-accent" aria-hidden="true"></div>
        <p class="overview-label">{{ card.label }}</p>
        <p class="overview-value">{{ overview[card.key] }}</p>
        <p class="overview-hint">{{ card.hint }}</p>
      </article>
    </div>
    <div v-else class="overview-state">暂无概览数据</div>
  </section>
</template>
