<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getJobs } from '../api/jobs'

const categoryOptions = ['后端开发', '数据分析', '数据开发', '算法', '测试', '其他']
const filters = reactive({ keyword: '', city: '', category: '', company: '' })
const jobs = ref([])
const currentPage = ref(1)
const pageSize = 10
const totalPages = ref(0)
const totalJobs = ref(0)
const loading = ref(true)
const error = ref('')

const canGoPrevious = computed(() => !loading.value && currentPage.value > 1)
const canGoNext = computed(() => !loading.value && currentPage.value < totalPages.value)

function requestParams() {
  const params = { page: currentPage.value, size: pageSize }
  for (const [key, value] of Object.entries(filters)) {
    if (value.trim()) params[key] = value.trim()
  }
  return params
}

async function loadJobs() {
  loading.value = true
  error.value = ''
  try {
    const result = await getJobs(requestParams())
    jobs.value = result.records ?? []
    currentPage.value = result.current ?? 1
    totalPages.value = result.pages ?? 0
    totalJobs.value = result.total ?? 0
  } catch (requestError) {
    error.value = '岗位数据加载失败'
    console.error('Failed to load jobs', requestError)
  } finally {
    loading.value = false
  }
}

function searchJobs() {
  currentPage.value = 1
  loadJobs()
}

function resetFilters() {
  Object.assign(filters, { keyword: '', city: '', category: '', company: '' })
  currentPage.value = 1
  loadJobs()
}

function previousPage() {
  if (!canGoPrevious.value) return
  currentPage.value -= 1
  loadJobs()
}

function nextPage() {
  if (!canGoNext.value) return
  currentPage.value += 1
  loadJobs()
}

function formatSalary(value) {
  return value == null ? '面议 / 未知' : `${Number(value).toLocaleString('zh-CN')} 元`
}

onMounted(loadJobs)
</script>

<template>
  <section class="panel jobs-panel" aria-labelledby="jobs-heading">
    <header class="panel-header jobs-header">
      <div>
        <p class="eyebrow">JOB EXPLORER</p>
        <h2 id="jobs-heading">岗位查询</h2>
        <p class="panel-note">查询与分页均由 Spring Boot API 执行</p>
      </div>
      <p class="jobs-total">共 <strong>{{ totalJobs }}</strong> 条</p>
    </header>

    <form class="job-filters" @submit.prevent="searchJobs">
      <label>
        <span>关键词</span>
        <input v-model="filters.keyword" type="search" placeholder="例如 Java" />
      </label>
      <label>
        <span>城市</span>
        <input v-model="filters.city" type="text" placeholder="例如 北京" />
      </label>
      <label>
        <span>岗位类别</span>
        <select v-model="filters.category">
          <option value="">全部类别</option>
          <option v-for="category in categoryOptions" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </label>
      <label>
        <span>公司</span>
        <input v-model="filters.company" type="text" placeholder="公司关键词" />
      </label>
      <div class="filter-actions">
        <button class="primary-button" type="submit" :disabled="loading">查询</button>
        <button class="secondary-button" type="button" :disabled="loading" @click="resetFilters">
          重置
        </button>
      </div>
    </form>

    <div v-if="loading" class="table-state">岗位数据加载中...</div>
    <div v-else-if="error" class="table-state error-state">
      <span>{{ error }}</span>
      <button class="text-button" type="button" @click="loadJobs">重新加载</button>
    </div>
    <div v-else-if="!jobs.length" class="table-state">没有找到符合条件的岗位</div>
    <template v-else>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>岗位名称</th>
              <th>公司</th>
              <th>城市</th>
              <th>类别</th>
              <th>学历</th>
              <th>最低月薪</th>
              <th>最高月薪</th>
              <th>发布日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs" :key="job.sourceId ?? job.id">
              <td class="job-title-cell">{{ job.title }}</td>
              <td>{{ job.company }}</td>
              <td>{{ job.city }}</td>
              <td><span class="category-chip">{{ job.category }}</span></td>
              <td>{{ job.education }}</td>
              <td>{{ formatSalary(job.salaryMin) }}</td>
              <td>{{ formatSalary(job.salaryMax) }}</td>
              <td>{{ job.publishDate || '未知' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="pagination">
        <button class="secondary-button" type="button" :disabled="!canGoPrevious" @click="previousPage">
          上一页
        </button>
        <p>第 <strong>{{ currentPage }}</strong> / {{ totalPages }} 页 · 共 {{ totalJobs }} 条</p>
        <button class="secondary-button" type="button" :disabled="!canGoNext" @click="nextPage">
          下一页
        </button>
      </footer>
    </template>
  </section>
</template>
