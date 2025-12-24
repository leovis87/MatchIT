import { SortOption } from './sortoption'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface BootcampItem {
    BootcampID: number
    Title: string
    InstituteName: string
    JobCategoryID: number
    CategoryName: string
    Location: string | null
    OnlineOffline: string
    CostSupportType: string
    EducationContent: string | null
    Qualification: string | null
    Benefits: string | null
    StartDate: string | null
    RegistrationDate: string | null
    CloseDate: string | null
    DetailUrl: string | null
    ViewCount: number
    CreatedAt: string
    UpdatedAt: string
}

export interface PaginatedBootcampResponse {
    total: number
    page: number
    size: number
    items: BootcampItem[]
}

export interface FilterOptionsResponse {
    categories: string[]
    modes: string[]
    fundings: string[]
}

export const bootcampApi = {
    getBootcamps: async (params: {
        page?: number
        size?: number
        show_expired?: boolean  // 마감일 추가
        sort?: SortOption  // 정렬 기준 추가
        keyword?: string
        category_id?: number
        category_names?: string[]
        online_offline?: string[]
        cost_support_type?: string[]
    }): Promise<PaginatedBootcampResponse> => {
        const queryParams = new URLSearchParams()
        Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            // 배열인 경우 각 항목을 개별적으로 추가
            if (Array.isArray(value)) {
                value.forEach(item => {
                    queryParams.append(key, String(item))
                })
            } else {
                queryParams.append(key, String(value))
            }
        }
    })

        const response = await fetch(`${API_BASE_URL}/bootcamps?${queryParams}`)
        if (!response.ok) throw new Error('Failed to fetch bootcamps')
        return response.json()
    },

    getBootcampDetail: async (id: number): Promise<BootcampItem> => {
        const response = await fetch(`${API_BASE_URL}/bootcamps/${id}`)
        if (!response.ok) throw new Error('Failed to fetch bootcamp detail')
        return response.json()
    },

    getFilterOptions: async (): Promise<FilterOptionsResponse> => {
        const response = await fetch(`${API_BASE_URL}/bootcamps/filter-options`)
        if (!response.ok) throw new Error('Failed to fetch filter options')
        return response.json()
    },
}