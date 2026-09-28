import http from './http'

export async function getOverview() {
  const response = await http.get('/statistics/overview')
  return response.data
}

export async function getSkills(params = {}) {
  const response = await http.get('/statistics/skills', { params })
  return response.data
}

export async function getCities() {
  const response = await http.get('/statistics/cities')
  return response.data
}

export async function getCategories() {
  const response = await http.get('/statistics/categories')
  return response.data
}

export async function getSalary() {
  const response = await http.get('/statistics/salary')
  return response.data
}
