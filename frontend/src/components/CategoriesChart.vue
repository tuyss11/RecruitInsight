<script setup>
import { onMounted, ref } from 'vue'
import { getCategories } from '../api/statistics'
import { useEChart } from '../composables/useEChart'

const categories = ref([])
const loading = ref(true)
const error = ref('')
const { chartElement, setChartOption, clearChart } = useEChart()

function buildOption(data) {
  const displayData = [...data].reverse()
  const detailByCategory = Object.fromEntries(data.map((item) => [item.category, item]))
  return {
    animationDuration: 450,
    color: ['#7a5af8'],
    grid: {
      left: 18,
      right: 32,
      top: 12,
      bottom: 18,
      outerBoundsMode: 'same',
      outerBoundsContain: 'axisLabel',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: ([item]) => {
        const detail = detailByCategory[item.name]
        return `${item.name}<br/>${detail.jobCount} 个岗位<br/>占比：${detail.percentage}%`
      },
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#edf0f5' } },
    },
    yAxis: {
      type: 'category',
      data: displayData.map((item) => item.category),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: '#475467' },
    },
    series: [{
      name: '岗位数量',
      type: 'bar',
      data: displayData.map((item) => item.jobCount),
      barMaxWidth: 24,
      itemStyle: { borderRadius: [0, 5, 5, 0] },
    }],
  }
}

async function loadCategories() {
  loading.value = true
  error.value = ''
  try {
    categories.value = await getCategories()
    loading.value = false
    if (categories.value.length) await setChartOption(buildOption(categories.value))
    else clearChart()
  } catch (requestError) {
    error.value = '类别数据加载失败'
    console.error('Failed to load category statistics', requestError)
  } finally {
    loading.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <article class="panel chart-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">CATEGORIES</p>
        <h2>岗位类别分布</h2>
        <p class="panel-note">数量与占比直接来自统计 API</p>
      </div>
    </header>
    <div v-if="loading" class="panel-state">类别数据加载中...</div>
    <div v-else-if="error" class="panel-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadCategories">重新加载</button>
    </div>
    <div v-else-if="!categories.length" class="panel-state">暂无类别数据</div>
    <div v-show="!loading && !error && categories.length" ref="chartElement" class="chart-canvas"></div>
  </article>
</template>
