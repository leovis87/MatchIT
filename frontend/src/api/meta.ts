const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const metaApi = {
  async getCareerLevels() {
    const url = `${API_BASE_URL}/careerlevels`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Get career levels failed: ${res.status}`)
    return res.json()
  },

  async getExperienceRanges() {
    const url = `${API_BASE_URL}/experienceranges`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Get experience ranges failed: ${res.status}`)
    return res.json()
  },

  async getDesiredJobs() {
    const url = `${API_BASE_URL}/desiredjobs`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Get desired jobs failed: ${res.status}`)
    return res.json()
  },

  async getStats() {
    const url = `${API_BASE_URL}/stats`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Get stats failed: ${res.status}`)
    return res.json()
  },
}