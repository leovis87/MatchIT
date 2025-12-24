const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const searchApi = {
  async search(keyword: string) {
    const url = `${API_BASE_URL}/search?keyword=${encodeURIComponent(keyword)}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Search request failed: ${res.status}`)
    return res.json()
  },

  async searchWithFilters(params: {
    keyword?: string
    skills?: string[]
    source?: '전체' | '채용' | '부트캠프'
    careerLevelId?: number
    experienceRangeId?: number
    limit?: number
    randomOrder?: boolean
    sort?: string
  }) {
    const queryParams = new URLSearchParams()

    if (params.keyword) queryParams.append('keyword', params.keyword)
    if (params.skills && params.skills.length > 0) {
      params.skills.forEach((skill) => queryParams.append('skills', skill))
    }
    if (params.source && params.source !== '전체') {
      queryParams.append('source', params.source)
    }
    if (params.careerLevelId) queryParams.append('career_level_id', params.careerLevelId.toString())
    if (params.experienceRangeId) queryParams.append('experience_range_id', params.experienceRangeId.toString())
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.randomOrder) queryParams.append('random_order', 'true')
    if (params.sort) queryParams.append('sort', params.sort)

    const url = `${API_BASE_URL}/search?${queryParams.toString()}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Search request failed: ${res.status}`)
    return res.json()
  },
}