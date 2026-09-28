<script setup>
import { onMounted, ref } from 'vue'
import { getSalary } from '../api/statistics'
import { useEChart } from '../composables/useEChart'

const salary = ref([])
const loading = ref(true)
const error = ref('')
const { chartElement, setChartOption, clearChart } = useEChart()

function buildOption(data) {
  return {
    animationDuration: 450,
    color: ['#9bb3ff', '#315efb', '#173ea5'],
    legend: {
      top: 0,
      right: 0,
      textStyle: { color: '#667085' },
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: {
      left: 18,
      right: 18,
      top: 48,
      bottom: 18,
      outerBoundsMode: 'same',
      outerBoundsContain: 'axisLabel',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => `${Number(value).toLocaleString('zh-CN')} 元/月`,
    },
    xAxis: {
      type: 'category',
      data: data.map((item) => item.category),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#d8dee8' } },
      axisLabel: { color: '#475467', interval: 0 },
    },
    yAxis: {
      type: 'value',
      name: '元/月',
      nameTextStyle: { color: '#98a2b3', align: 'right' },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#edf0f5' } },
      axisLabel: { color: '#667085', formatter: (value) => `${value / 1000}k` },
    },
    series: [
      {
        name: '平均最低',
        type: 'bar',
        data: data.map((item) => item.averageSalaryMin),
        barMaxWidth: 22,
      },
      {
        name: '平均中点',
        type: 'bar',
        data: data.map((item) => item.averageSalaryMid),
        barMaxWidth: 22,
      },
      {
        name: '平均最高',
        type: 'bar',
        data: data.map((item) => item.averageSalaryMax),
        barMaxWidth: 22,
      },
    ],
  }
}

async function loadSalary() {
  loading.value = true
  error.value = ''
  try {
    salary.value = await getSalary()
    loading.value = false
    if (salary.value.length) await setChartOption(buildOption(salary.value))
    else clearChart()
  } catch (requestError) {
    error.value = '薪资数据加载失败'
    console.error('Failed to load salary statistics', requestError)
  } finally {
    loading.value = false
  }
}

onMounted(loadSalary)
</script>

<template>
  <article class="panel chart-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">SALARY</p>
        <h2>各岗位类别月薪对比</h2>
        <p class="panel-note">仅统计薪资上下界完整的岗位，单位为人民币元/月</p>
      </div>
    </header>
    <div v-if="loading" class="panel-state">薪资数据加载中...</div>
    <div v-else-if="error" class="panel-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadSalary">重新加载</button>
    </div>
    <div v-else-if="!salary.length" class="panel-state">暂无有效薪资数据</div>
    <div v-show="!loading && !error && salary.length" ref="chartElement" class="chart-canvas salary-canvas"></div>
  </article>
</template>
