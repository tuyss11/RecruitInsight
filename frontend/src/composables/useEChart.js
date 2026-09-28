import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { BarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

export function useEChart() {
  const chartElement = ref(null)
  let chartInstance = null

  const resizeChart = () => chartInstance?.resize()

  const setChartOption = async (option) => {
    await nextTick()
    if (!chartElement.value) return
    if (!chartInstance) chartInstance = echarts.init(chartElement.value)
    chartInstance.setOption(option, { notMerge: true })
  }

  const clearChart = () => chartInstance?.clear()

  onMounted(() => window.addEventListener('resize', resizeChart))
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeChart)
    chartInstance?.dispose()
    chartInstance = null
  })

  return { chartElement, setChartOption, clearChart }
}
