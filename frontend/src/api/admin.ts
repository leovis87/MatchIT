import type { AdminBootcamp, BootcampUpdatePayload } from '../types/bootcamp'

export interface AdminJobUpdatePayload {
  Title?: string | null
  CompanyName?: string | null
  JobCategoryID?: number | null
  EmploymentType?: string | null
  ExperienceRequirement?: string | null
  MinExperienceYears?: number | null
  EducationRequirement?: string | null
  Location?: string | null
  MainTasks?: string | null
  Qualifications?: string | null
  Preferences?: string | null
  Benefits?: string | null
  Process?: string | null
  Salary?: string | null
  PostedDate?: string | null
  CloseDate?: string | null
  Url?: string | null
  IsActive?: boolean | null
  PlatformID?: number | null
}

export interface AdminBootcampUpdatePayload {
  Title?: string | null
  InstituteName?: string | null
  JobCategoryID?: number | null
  Location?: string | null
  OnlineOffline?: string | null
  CostSupportType?: string | null
  EducationContent?: string | null
  Qualification?: string | null
  Benefits?: string | null
  StartDate?: string | null
  RegistrationDate?: string | null
  CloseDate?: string | null
  DetailUrl?: string | null
  ViewCount?: number | null
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 회원 관리 API
export const adminApi = {
  // ========== 회원 관리 ==========
  async getUsers() {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to get users: ${response.status}`)
    return response.json()
  },

  async deleteUser(userId: number) {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to delete user: ${response.status}`)
    return response.json()
  },

  async updateUserRole(userId: number, role: number) {
    // 다양한 백엔드 라우트/메서드/바디 조합을 순차 시도 (404/405 대응)
    const headers = { 'Content-Type': 'application/json' }
    const roleId = role;
    // 백엔드가 roleid를 int로 기대하므로 roleid: roleId로 전송
    const payloads = [
      { roleid: roleId },
    ]
    const urls = [
      `${API_BASE_URL}/admin/users/${userId}/role`,
    ]
    const methods: Array<'PATCH' | 'PUT' | 'POST'> = ['PATCH', 'PUT', 'POST']

    let lastStatus = 0
    let lastBody = ''

    for (const url of urls) {
      for (const method of methods) {
        for (const payload of payloads) {
          const response = await fetch(url, {
            method,
            credentials: 'include',
            headers,
            body: JSON.stringify(payload),
          })

          if (response.ok) {
            return response.json()
          }

          lastStatus = response.status
          try {
            lastBody = await response.text()
          } catch {
            lastBody = ''
          }

          // 404/405만 다음 조합으로 계속 시도, 그 외 에러는 즉시 반환
          if (![404, 405].includes(response.status)) {
            throw new Error(`Failed to update user role: ${response.status} ${lastBody}`)
          }
        }
      }
    }

    throw new Error(`Failed to update user role: ${lastStatus} ${lastBody}`)
  },

  // ========== 채용 공고 관리 ==========
  async getJobPosts() {
    const response = await fetch(`${API_BASE_URL}/admin/jobposts`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to get job posts: ${response.status}`)
    return response.json()
  },

  async deleteJobPost(jobId: number) {
    const response = await fetch(`${API_BASE_URL}/admin/jobposts/${jobId}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to delete job post: ${response.status}`)
    return response.json()
  },

  async updateJobPost(jobId: number, data: { jobtitle?: string; jobdescription?: string }) {
    const response = await fetch(`${API_BASE_URL}/admin/jobposts/${jobId}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`Failed to update job post: ${response.status}`)
    return response.json()
  },

  async updateFullJobPost(jobId: number, data: AdminJobUpdatePayload) {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) throw new Error(`Failed to update job post: ${response.status}`)
    return response.json()
  },

  // ========== 부트캠프 관리 ==========
  async getBootcamps(): Promise<AdminBootcamp[]> {
    const response = await fetch(`${API_BASE_URL}/admin/bootcamps`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to get bootcamps: ${response.status}`)
    return response.json()
  },

  async deleteBootcamp(bootcampId: number) {
    const response = await fetch(`${API_BASE_URL}/admin/bootcamps/${bootcampId}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error(`Failed to delete bootcamp: ${response.status}`)
    return response.json()
  },

  async updateBootcamp(bootcampId: number, data: BootcampUpdatePayload) {
    const response = await fetch(`${API_BASE_URL}/admin/bootcamps/${bootcampId}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`Failed to update bootcamp: ${response.status}`)
    return response.json()
  },

  async updateFullBootcamp(bootcampId: number, data: AdminBootcampUpdatePayload) {
    const response = await fetch(`${API_BASE_URL}/bootcamps/${bootcampId}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) throw new Error(`Failed to update bootcamp: ${response.status}`)
    return response.json()
  },
}
