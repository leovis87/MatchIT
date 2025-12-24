import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { bootcampApi, type BootcampItem } from '../services/bootcampApi'
import { useNavigate } from 'react-router-dom'

type Bootcamp = {
  id: string
  name: string
  provider: string
  field: string
  mode: '온라인' | '오프라인' | '혼합'
  price: string
  funding: '국비지원' | '본인부담'
  duration: string
  // level: '입문' | '중급' | '고급'
  curriculum: string  // 커리큘럼 전체 텍스트
  closeDate: string | null  // 마감일 (필터링용)
}

// 날짜 차이 계산 (주 단위)
const calculateDuration = (startDate: string | null, closeDate: string | null): string => {
  if (!startDate || !closeDate) return '-'

  const start = new Date(startDate)
  const close = new Date(closeDate)

  if (isNaN(start.getTime()) || isNaN(close.getTime())) return '-'

  const diffTime = Math.abs(close.getTime() - start.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  const diffWeeks = Math.ceil(diffDays / 7)

  return `${diffWeeks}주`
}

/**
 * 마감일이 지났는지 확인
 * @param closeDate - 오픈일 문자열
 * @returns true: 마감됨, false: 진행 중
 */
const isExpired = (closeDate: string | null): boolean => {
  if (!closeDate) return false // 마감일 정보 없으면 진행 중으로 간주

  const close = new Date(closeDate)
  if (isNaN(close.getTime())) return false

  const today = new Date()
  today.setHours(0, 0, 0, 0) // 시간 부분 제거 (오늘 00:00:00)

  return close < today // 마감일이 오늘보다 이전이면 true
}

/**
 * 백엔드 데이터를 프론트엔드 형식으로 변환
 *
 * @param item - 백엔드 API에서 받은 부트캠프 데이터
 * @returns 프론트엔드에서 사용할 Bootcamp 타입 객체
 *
 * 주의: DB 제약조건과 일치하도록 매핑
 * - OnlineOffline: '온라인', '오프라인', '혼합형' (DB에 '혼합형'으로 저장됨)
 * - CostSupportType: '국비지원', '본인부담'
 */
const mapBackendToFrontend = (item: BootcampItem): Bootcamp => {
  // OnlineOffline 변환: DB의 '혼합형'을 '혼합'으로 변환
  let mode: Bootcamp['mode'] = '혼합'
  if (item.OnlineOffline === '온라인') mode = '온라인'
  else if (item.OnlineOffline === '오프라인') mode = '오프라인'
  else if (item.OnlineOffline === '혼합형') mode = '혼합'

  return {
    id: String(item.BootcampID),
    name: item.Title,
    provider: item.InstituteName,
    field: item.CategoryName,  // DB의 CategoryName을 그대로 사용
    mode: mode,
    price: item.CostSupportType === '국비지원' ? '국비지원' : '본인부담',
    funding: item.CostSupportType === '국비지원' ? '국비지원' : '본인부담',
    duration: calculateDuration(item.StartDate, item.CloseDate),
    // level: '입문',
    curriculum: item.EducationContent || '',  // 커리큘럼 텍스트 그대로 사용
    closeDate: item.CloseDate,  // 마감일 필터링용
  }
}

// 필터 옵션은 동적으로 생성됩니다 (아래 useMemo 참조)

/**
 * 텍스트를 지정된 길이로 자르고 "..." 추가
 */
const truncateText = (text: string,
                      maxLength: number): string => {
  if (!text || text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

const BootcampsPage = () => {
  const [bootcamps, setBootcamps] = useState<Bootcamp[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [total, setTotal] = useState(0)

  // ✅ 필터 옵션용 전체 목록 (별도로 관리)
  const [allFields, setAllFields] = useState<string[]>([])
  const [allModes, setAllModes] = useState<Bootcamp['mode'][]>([])
  const [allFundings, setAllFundings] = useState<Bootcamp['funding'][]>([])

  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set())
  const [selectedModes, setSelectedModes] = useState<Set<Bootcamp['mode']>>(new Set())
  const [selectedFunding, setSelectedFunding] = useState<Set<Bootcamp['funding']>>(new Set())
  // const [selectedLevels, setSelectedLevels] = useState<Set<Bootcamp['level']>>(new Set())

  // 마감된 공고 표시 여부
  const [showExpired, setShowExpired] = useState(false)

  /**
   * 페이지네이션 상태
   *
   * currentPage: 현재 보고 있는 페이지 번호 (1부터 시작)
   * itemsPerPage: 한 페이지에 표시할 부트캠프 개수
   *
   * 페이지당 항목 수를 변경하려면 itemsPerPage 값을 수정하세요.
   * 예: const itemsPerPage = 20
   */
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10 // 페이지당 표시할 아이템 수
  const [sort, setSort] = useState<'created' | 'deadline' | 'views'>('created') // 정렬 상태 추가

  /**
   * 백엔드에서 데이터 가져오기
   *
   * 컴포넌트가 마운트될 때 한 번만 실행됩니다.
   * size: 100으로 설정하여 최대 100개의 부트캠프를 가져옵니다.
   *
   * 서버 사이드 페이지네이션으로 변경하려면:
   * - useEffect 의존성에 currentPage 추가
   * - API 호출에 page: currentPage 전달
   */

  // ✅ 초기 로딩: 필터 옵션만 가져오기 (한 번만 실행)
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        // 백엔드의 /filter-options API 호출
        const options = await bootcampApi.getFilterOptions()

        // 전체 필터 옵션 저장
        setAllFields(options.categories)
        setAllModes(options.modes.map(m =>
          m === '혼합형' ? '혼합' : m
        ) as Bootcamp['mode'][])
        setAllFundings(options.fundings as Bootcamp['funding'][])
      } catch (err) {
        console.error('필터 옵션 로딩 실패: ', err)
      }
    }
    fetchFilterOptions()
  }, []) // 빈 배열 = 컴포넌트 마운트 시 한 번만 실행

  // ✅ 데이터 가져오기 (필터 적용)
  useEffect(() => {
    const fetchBootcamps = async () => {
      try {
        setLoading(true)
        const response = await bootcampApi.getBootcamps({ 
          page: currentPage,          // 현제 페이지 번호전달
          size: itemsPerPage,         // 페이지당 항목 수 전달
          show_expired: showExpired,  // 마감일 추가
          sort: sort,                 // 정렬 기준 추가
          online_offline: selectedModes.size > 0
            ? Array.from(selectedModes).map(m => m === '혼합' ? '혼합형': m)
            : undefined,
          cost_support_type: selectedFunding.size > 0
            ? Array.from(selectedFunding)
            : undefined,
          category_names: selectedFields.size > 0 //추가
            ? Array.from(selectedFields)
            : undefined
        })
        const mapped = response.items.map(mapBackendToFrontend)
        setBootcamps(mapped)
        setTotal(response.total)  // ✅ 서버 total 저장
        setError(null)

        // // 🔍 디버깅: 실제 데이터 확인
        // console.log('📊 첫 3개 부트캠프 데이터:', mapped.slice(0, 3))
        // console.log('📊 실제 field 값들:', [...new Set(mapped.map(b => b.field))])
        // console.log('📊 실제 mode 값들:', [...new Set(mapped.map(b => b.mode))])
        // console.log('📊 실제 funding 값들:', [...new Set(mapped.map(b => b.funding))])
      } catch (err) {
        setError('부트캠프 데이터를 불러오는데 실패했습니다.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchBootcamps()
  }, [currentPage, itemsPerPage, showExpired, sort, selectedModes, selectedFunding, selectedFields]) // ✅ sort가 바뀔 때마다 다시 호출

  const getInitialCompare = () => {
    try {
      if (typeof window === 'undefined') return []
      const raw = localStorage.getItem('compare_bootcamps')
      return raw ? (JSON.parse(raw) as Bootcamp[]) : []
    } catch {
      return []
    }
  }

  const [compareList, setCompareList] = useState<Bootcamp[]>(getInitialCompare)

  useEffect(() => {
    try {
      localStorage.setItem('compare_bootcamps', JSON.stringify(compareList))
    } catch {}
  }, [compareList])

  const navigate = useNavigate()

  const addToCompare = (boot: Bootcamp) => {
    setCompareList((prev) => {
      if (prev.find((b) => b.id === boot.id)) {
        window.alert('이미 비교함에 담긴 부트캠프입니다.')
        return prev
      }
      if (prev.length >= 3) {
        window.alert('비교함은 최대 3개까지 담을 수 있습니다.')
        return prev
      }
      return [...prev, boot]
    })
  }

  const removeFromCompare = (id: string) => setCompareList((prev) => prev.filter((b) => b.id !== id))

  const clearCompare = () => setCompareList([])

  const toggleSet = <T,>(value: T, setter: React.Dispatch<React.SetStateAction<Set<T>>>) => {
    setter((prev) => {
      const next = new Set(prev)
      next.has(value) ? next.delete(value) : next.add(value)
      return next
    })
  }

  const resetAllFilters = () => {
    setSelectedFields(new Set())
    setSelectedModes(new Set())
    setSelectedFunding(new Set())
    setShowExpired(false)
    setCurrentPage(1)
  }

  useEffect(() => {
    setCurrentPage(1)
  }, [selectedFields, selectedModes, selectedFunding])

  const totalPages = Math.ceil(total / itemsPerPage)
  const currentBootcamps = bootcamps // 🛠️ slice 필요없음

  const getPageNumbers = () => {
    const pages: number[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i)
        pages.push(-1) // ... 표시용
        pages.push(totalPages)
      } else if (currentPage >= totalPages - 2) {
        pages.push(1)
        pages.push(-1)
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i)
      } else {
        pages.push(1)
        pages.push(-1)
        pages.push(currentPage - 1)
        pages.push(currentPage)
        pages.push(currentPage + 1)
        pages.push(-1)
        pages.push(totalPages)
      }
    }

    return pages
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">로딩 중...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-12 md:px-6">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-semibold text-primary-700">부트캠프 리스트</p>
          <h1 className="text-2xl font-bold text-slate-950 sm:text-3xl">내게 맞는 부트캠프 찾아보기</h1>
          <p className="text-sm text-slate-600">
            분야, 수강 형태, 가격대를 선택해 원하는 과정을 빠르게 탐색하세요.
          </p>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-2xl border border-slate-100 bg-slate-50/80 p-5 shadow-soft">
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">분야</h3>
                <div className="mt-3 space-y-2">
                  {allFields.map((field) => (
                    <label key={field} className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={selectedFields.has(field)}
                        onChange={() => toggleSet(field, setSelectedFields)}
                        className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      {field}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-900">수강 형태</h3>
                <div className="mt-3 space-y-2">
                  {allModes.map((mode) => (
                    <label key={mode} className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={selectedModes.has(mode)}
                        onChange={() => toggleSet(mode, setSelectedModes)}
                        className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      {mode}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-900">가격/지원</h3>
                <div className="mt-3 space-y-2">
                  {allFundings.map((fund) => (
                    <label key={fund} className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={selectedFunding.has(fund)}
                        onChange={() => toggleSet(fund, setSelectedFunding)}
                        className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      {fund}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-900">마감 공고</h3>
                <div className="mt-3 space-y-2">
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={showExpired}
                      onChange={(e) => setShowExpired(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                    마감된 공고 보기
                  </label>
                </div>
              </div>

              <div>
                <button
                  onClick={resetAllFilters}
                  className="mt-2 text-xs font-semibold text-primary-700 underline"
                >
                  필터 전체 초기화
                </button>
              </div>
            </div>
          </aside>

          <section className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-semibold text-slate-800">
                총 {total}건
              </p>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as 'created' | 'deadline' | 'views')}
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                <option value="created">최신 등록순</option>
                <option value="deadline">마감일</option>
                <option value="views">조회수</option>
              </select>
            </div>

            <div className="space-y-4">
              {currentBootcamps.map((boot) => (
                <div
                  key={boot.id}
                  className="flex flex-col gap-3 rounded-2xl border border-slate-100 bg-white p-5 shadow-soft md:flex-row md:items-center md:justify-between"
                >
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-primary-700">{boot.provider}</p>
                    <h3 className="text-lg font-bold text-slate-900 hover:underline"><Link to={`/bootcamps/${boot.id}`}>{boot.name}</Link></h3>
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600">
                      <span className="rounded-full bg-slate-100 px-3 py-1">{boot.field}</span>
                      <span className="rounded-full bg-slate-100 px-3 py-1">{boot.mode}</span>
                      <span className="rounded-full bg-slate-100 px-3 py-1">{boot.price}</span>
                      <span className="rounded-full bg-slate-100 px-3 py-1">{boot.funding}</span>
                      <span className="rounded-full bg-slate-100 px-3 py-1">{boot.duration}</span>
                    </div>
                    {boot.curriculum && (
                      <div className="mt-2">
                        <p className="text-xs text-slate-600 leading-relaxed">
                          {truncateText(boot.curriculum, 50)}
                        </p>
                        <span className="text-xs text-slate-600">
                          <strong>마감일: {(boot.closeDate && boot.closeDate.split('T')[0]) || '상시'}</strong>
                        </span>
                      </div>
                      
                    )}
                  </div>
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        addToCompare(boot)
                      }}
                      className="w-full rounded-xl border border-primary-200 px-4 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-50 md:w-[140px] md:justify-center"
                    >
                      {compareList.find((j) => j.id === boot.id) ? '추가됨' : '비교 담기'}
                    </button>
                  </div>
                </div>
              ))}
              {!bootcamps.length && !loading && (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
                  조건에 맞는 부트캠프가 없습니다. 필터를 조정하거나 초기화해주세요.
                </div>
              )}
            </div>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-4">
                <button
                  onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
                >
                  이전
                </button>

                {getPageNumbers().map((pageNum, idx) => {
                  if (pageNum === -1) {
                    return (
                      <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">
                        ...
                      </span>
                    )
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`min-w-[40px] rounded-lg border px-3 py-2 text-sm font-medium transition ${
                        currentPage === pageNum
                          ? 'border-primary-600 bg-primary-600 text-white'
                          : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}

                <button
                  onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
                >
                  다음
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
              {compareList.length > 0 && (
                <aside className="fixed right-6 top-24 w-80 max-h-[70vh] overflow-auto bg-white border border-slate-100 rounded-2xl p-4 shadow-lg z-50">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold text-slate-900">비교함 ({compareList.length}/3)</h4>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={clearCompare}
                          className="text-xs font-semibold text-red-600 hover:underline"
                        >
                          전체삭제
                        </button>
                      </div>
                    </div>

                  <div className="space-y-3">
                          {compareList.map((item) => (
                            <div key={item.id} className="flex items-start justify-between gap-2 p-2 border rounded-lg">
                              <div>
                                <p className="text-xs font-semibold text-primary-700">{item.provider}</p>
                                <p className="text-sm font-bold text-slate-900">{item.name}</p>
                                <p className="text-xs text-slate-600">{item.price}</p>
                              </div>
                              <div className="flex flex-col items-end gap-2">
                                <button
                                  onClick={() => removeFromCompare(item.id)}
                                  className="whitespace-nowrap text-xs font-semibold text-primary-700 hover:underline flex-shrink-0"
                                >
                                  삭제
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>

                        <div className="mt-3 flex justify-end">
                          <button
                            onClick={() => {
                              const ids = compareList.map((b) => b.id).join(',')
                              navigate(`/compare?mode=bootcamps&ids=${encodeURIComponent(ids)}`)
                            }}
                            className="text-sm font-semibold text-white bg-primary-600 px-3 py-2 rounded-md hover:bg-primary-700"
                          >
                            비교하기
                          </button>
                        </div>
                      </aside>
                    )}

            </div>
  )
}

export default BootcampsPage

