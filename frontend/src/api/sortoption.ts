// 공통 정렬 옵션 타입
export type SortOption = 'created' | 'deadline' | 'views'

// 정렬 옵션 정의
export const SortOption = {
  created: 'created' as const,
  deadline: 'deadline' as const,
  views: 'views' as const,
} as const