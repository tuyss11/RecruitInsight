import http from './http'

export async function getJobs(params = {}) {
  const response = await http.get('/jobs', { params })
  return response.data
}
