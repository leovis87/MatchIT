const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const skillsApi = {
  async getAllSkills() {
    const url = `${API_BASE_URL}/skills/all`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Get all skills failed: ${res.status}`)
    return res.json()
  },

  async autocomplete(query: string) {
    const url = `${API_BASE_URL}/skills?query=${encodeURIComponent(query)}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Skills autocomplete failed: ${res.status}`)
    return res.json()
  },
}