<script setup>
import { onMounted, ref } from 'vue'
import { getCities } from '../api/statistics'
import { useEChart } from '../composables/useEChart'

const cities = ref([])
const loading = ref(true)
const error = ref('')
const { chartElement, setChartOption, clearChart } = useEChart()

function buildOption(data) {
  return {
    animationDuration: 450,
    color: ['#12a594'],
    grid: {
      left: 18,
      right: 18,
      top: 18,
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
      type: 'category',
      data: data.map((item) => item.city),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#d8dee8' } },
      axisLabel: { color: '#475467', interval: 0 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#edf0f5' } },
    },
    series: [{
      name: '岗位数量',
      type: 'bar',
      data: data.map((item) => item.jobCount),
      barMaxWidth: 34,
      itemStyle: { borderRadius: [5, 5, 0, 0] },
    }],
  }
}

async function loadCities() {
  loading.value = true
  error.value = ''
  try {
    cities.value = await getCities()
    loading.value = false
    if (cities.value.length) await setChartOption(buildOption(cities.value))
    else clearChart()
  } catch (requestError) {
    error.value = '城市数据加载失败'
    console.error('Failed to load city statistics', requestError)
  } finally {
    loading.value = false
  }
}

onMounted(loadCities)
</script>

<template>
  <article class="panel chart-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">CITIES</p>
        <h2>城市岗位数量</h2>
        <p class="panel-note">保留数据中的全部城市，包括“未知”</p>
      </div>
    </header>
    <div v-if="loading" class="panel-state">城市数据加载中...</div>
    <div v-else-if="error" class="panel-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadCities">重新加载</button>
    </div>
    <div v-else-if="!cities.length" class="panel-state">暂无城市数据</div>
    <div v-show="!loading && !error && cities.length" ref="chartElement" class="chart-canvas"></div>
  </article>
</template>
