<script setup>
import { onMounted, ref } from 'vue'
import { getSkills } from '../api/statistics'
import { useEChart } from '../composables/useEChart'

const categories = ['全部', '后端开发', '数据分析', '数据开发', '算法', '测试', '其他']
const selectedCategory = ref('全部')
const loading = ref(true)
const error = ref('')
const skills = ref([])
const { chartElement, setChartOption, clearChart } = useEChart()

function buildOption(data) {
  const displayData = [...data].reverse()
  return {
    animationDuration: 450,
    color: ['#315efb'],
    grid: {
      left: 18,
      right: 28,
      top: 12,
      bottom: 18,
      outerBoundsMode: 'same',
      outerBoundsContain: 'axisLabel',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: ([item]) => `${item.name}<br/>岗位数量：${item.value}`,
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#edf0f5' } },
    },
    yAxis: {
      type: 'category',
      data: displayData.map((item) => item.name),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: '#475467' },
    },
    series: [{
      name: '岗位数量',
      type: 'bar',
      data: displayData.map((item) => item.jobCount),
      barMaxWidth: 18,
      itemStyle: { borderRadius: [0, 5, 5, 0] },
    }],
  }
}

async function loadSkills() {
  loading.value = true
  error.value = ''
  try {
    const params = { limit: 10 }
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value
    skills.value = await getSkills(params)
    loading.value = false
    if (skills.value.length) await setChartOption(buildOption(skills.value))
    else clearChart()
  } catch (requestError) {
    error.value = '技能数据加载失败'
    console.error('Failed to load skill statistics', requestError)
  } finally {
    loading.value = false
  }
}

onMounted(loadSkills)
</script>

<template>
  <article class="panel chart-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">SKILLS</p>
        <h2>热门技能 Top 10</h2>
        <p class="panel-note">当前模拟数据中的技能需求频次</p>
      </div>
      <label class="chart-filter">
        <span>岗位类别</span>
        <select v-model="selectedCategory" aria-label="筛选技能岗位类别" @change="loadSkills">
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </label>
    </header>
    <div v-if="loading" class="panel-state">技能数据加载中...</div>
    <div v-else-if="error" class="panel-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadSkills">重新加载</button>
    </div>
    <div v-else-if="!skills.length" class="panel-state">当前类别暂无技能数据</div>
    <div v-show="!loading && !error && skills.length" ref="chartElement" class="chart-canvas"></div>
  </article>
</template>
