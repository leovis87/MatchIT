const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const usersApi = {
  async getMyProfile() {
    const url = `${API_BASE_URL}/users/me`
    const res = await fetch(url, {
      method: 'GET',
      credentials: 'include',
    })
    if (!res.ok) throw new Error(`Get my profile failed: ${res.status}`)
    return res.json()
  },

  async updateMyProfile(data: any) {
    const url = `${API_BASE_URL}/users/me`
    const res = await fetch(url, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(`Update my profile failed: ${res.status}`)
    return res.json()
  },

  async getScraps(userId: number) {
    const url = `${API_BASE_URL}/users/${userId}/scraps`
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error(`Get scraps failed: ${res.status}`)
    return res.json()
  },

  async getMyScraps() {
    const url = `${API_BASE_URL}/users/me/scraps`
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error(`Get my scraps failed: ${res.status}`)
    return res.json()
  },

  async addMyScrap(postType: 'Job' | 'Bootcamp', targetId: number) {
    const url = `${API_BASE_URL}/users/me/scraps`
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_type: postType, target_id: targetId }),
    })
    if (!res.ok) throw new Error(`Add scrap failed: ${res.status}`)
    return res.json()
  },

  async removeMyScrap(postType: 'Job' | 'Bootcamp', targetId: number) {
    const url = `${API_BASE_URL}/users/me/scraps`
    const res = await fetch(url, {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_type: postType, target_id: targetId }),
    })
    if (!res.ok) throw new Error(`Remove scrap failed: ${res.status}`)
    return res.json()
  },

  async getNotifications(userId: number) {
    const url = `${API_BASE_URL}/users/${userId}/notifications`
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error(`Get notifications failed: ${res.status}`)
    return res.json()
  },
}