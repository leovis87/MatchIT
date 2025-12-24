import { type ReactNode, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { skillsApi, metaApi, searchApi } from '../services/apiService'


// 아이콘 SVG 컴포넌트 (의존성 제거를 위해 인라인 정의)
const SearchIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 21L15.0001 15.0001M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

type Step = {
  title: string
  description: string
}

type PreviewItem = {
  title: string
  company: string
  tag: string
  type: '채용' | '부트캠프'
}

type Recommendation = {
  title: string
  description: string
  tags: string[]
}

const StepCard = ({ step, index, children, className }: { step: Step; index: number; children: ReactNode; className?: string }) => (
  <div className={`rounded-2xl border border-slate-100 bg-white/90 p-6 shadow-soft ${className}`}>
    <div className="flex items-start gap-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-sm font-semibold text-primary-700">
        {index}
      </div>
      <div className="w-full space-y-2">
        <div className="text-sm font-semibold text-primary-700">STEP {index}</div>
        <h3 className="text-lg font-bold text-slate-900">{step.title}</h3>
        <p className="text-sm text-slate-600">{step.description}</p>
        {children}
      </div>
    </div>
  </div>
)

const HomePage = () => {
  const navigate = useNavigate()
  const [isSkillSearchOpen, setIsSkillSearchOpen] = useState(false)
  
  // 스킬 목록 
  const [allSkills, setAllSkills] = useState<string[]>([])
  const [loadingSkills, setLoadingSkills] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const data = await skillsApi.getAllSkills()
        setAllSkills(data.skills)
      } catch (error) {
        console.error('Failed to fetch skills:', error)
        setAllSkills([])
      } finally {
        setLoadingSkills(false)
      }
    }

    fetchSkills()
  }, [])

  const [selectedStacks, setSelectedStacks] = useState<string[]>([])

  // DB-driven career levels & experience ranges
  const [careerLevels, setCareerLevels] = useState<any[]>([])
  const [experienceRanges, setExperienceRanges] = useState<any[]>([])
  const [loadingMeta, setLoadingMeta] = useState(true)

  // Stats for job posts and bootcamps
  const [jobCount, setJobCount] = useState<number>(0)
  const [bootcampCount, setBootcampCount] = useState<number>(0)

  const [selectedSource, setSelectedSource] = useState<'전체' | '채용'|'부트캠프'>('전체')
  const [selectedCareerLevelId, setSelectedCareerLevelId] = useState<number | null>(null)
  const [selectedExperienceRangeId, setSelectedExperienceRangeId] = useState<number | null>(null)

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const [cls, ers] = await Promise.all([
          metaApi.getCareerLevels().catch((e) => {
            console.error(e); return []
          }),
          metaApi.getExperienceRanges().catch((e) => {
            console.error(e); return []
          }),
        ])

        // try to normalize possible shapes
        const careerList = Array.isArray(cls) ? cls : (cls && cls.careerlevels) ? cls.careerlevels : []
        const expList = Array.isArray(ers) ? ers : (ers && ers.experienceranges) ? ers.experienceranges : []

        setCareerLevels(careerList)
        setExperienceRanges(expList)

        if (careerList.length > 0 && selectedCareerLevelId === null) {
          setSelectedCareerLevelId(careerList[0].id ?? careerList[0].CareerLevelID ?? null)
        }
        if (expList.length > 0 && selectedExperienceRangeId === null) {
          setSelectedExperienceRangeId(expList[0].id ?? expList[0].RangeID ?? null)
        }
      } finally {
        setLoadingMeta(false)
      }
    }

    fetchMeta()
  }, [])

  const previewItems: PreviewItem[] = [
    { title: '프론트엔드 엔지니어', company: '핀테크 스타트업', tag: 'React · TS', type: '채용' },
    { title: '백엔드 부트캠프', company: '클라우드 집중 과정', tag: 'Spring · AWS', type: '부트캠프' },
    { title: '풀스택 포지션', company: '커머스 스케일업', tag: 'Next.js · Node', type: '채용' },
  ]
  
  // 추천 결과 상태
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loadingRecommendations, setLoadingRecommendations] = useState(true)

  // DB에서 랜덤 채용공고와 부트캠프공고 가져오기
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoadingRecommendations(true)
        
        // 채용공고 2개 가져오기
        const jobsResponse = await searchApi.searchWithFilters({
          source: '채용',
          limit: 2,
          randomOrder: true,
        })
        
        // 부트캠프공고 2개 가져오기
        const bootcampsResponse = await searchApi.searchWithFilters({
          source: '부트캠프',
          limit: 2,
          randomOrder: true,
        })

        const jobs = jobsResponse.jobs || []
        const bootcamps = bootcampsResponse.bootcamps || []

        // 채용공고를 Recommendation 형태로 변환
        const jobRecommendations: Recommendation[] = jobs.slice(0, 2).map((job: any) => ({
          title: job.title || '채용공고',
          description: job.main_tasks 
            ? (job.main_tasks.length > 100 ? job.main_tasks.slice(0, 100) + '...' : job.main_tasks)
            : `${job.company_name || ''}에서 ${job.title || ''} 포지션을 모집 중입니다.`,
          tags: job.skills && job.skills.length > 0 
            ? job.skills.slice(0, 3) 
            : ['채용', job.job_category || 'IT'].filter(Boolean),
        }))

        // 부트캠프공고를 Recommendation 형태로 변환
        const bootcampRecommendations: Recommendation[] = bootcamps.slice(0, 2).map((bootcamp: any) => ({
          title: bootcamp.title || '부트캠프',
          description: bootcamp.education_content
            ? (bootcamp.education_content.length > 100 ? bootcamp.education_content.slice(0, 100) + '...' : bootcamp.education_content)
            : `${bootcamp.institute_name || ''}에서 제공하는 ${bootcamp.title || ''} 과정입니다.`,
          tags: ['부트캠프', bootcamp.location || '온라인', bootcamp.cost_support_type || '국비'].filter(Boolean),
        }))

        // 상단 2개는 채용공고, 하단 2개는 부트캠프공고로 합치기
        setRecommendations([...jobRecommendations, ...bootcampRecommendations])
      } catch (error) {
        console.error('Failed to fetch recommendations:', error)
        // 에러 발생 시 기본값 설정
        setRecommendations([
          {
            title: '초보 Python 개발자에게 인기 있는 채용 포지션',
            description: '웹 크롤링/ETL 경험이 있으면 우대, Django·FastAPI 기반 서비스 운영 팀.',
            tags: ['백엔드', 'Python', 'Django'],
          },
          {
            title: 'AI 서비스 PoC 경험을 쌓을 수 있는 스타트업 포지션',
            description: 'LLM API 연동, RAG 파이프라인 구축 경험자를 우대하는 초기팀.',
            tags: ['AI', 'LLM', 'Vector DB'],
          },
          {
            title: '데이터 분석 입문자를 위한 국비 부트캠프',
            description: '기초 파이썬부터 SQL, Tableau 대시보드까지 12주 완주 커리큘럼.',
            tags: ['데이터', 'SQL', '시각화'],
          },
          {
            title: '클라우드 기반 백엔드 부트캠프',
            description: 'AWS 기반 CI/CD와 마이크로서비스 아키텍처를 실습 중심으로 학습.',
            tags: ['백엔드', 'AWS', 'DevOps'],
          },
        ])
      } finally {
        setLoadingRecommendations(false)
      }
    }

    fetchRecommendations()
  }, [])

  const toggleStack = (stack: string) => {
    if (selectedStacks.includes(stack)) {
      setSelectedStacks(prev => prev.filter(s => s !== stack))
    } else {
      setSelectedStacks(prev => [...prev, stack])
    }
  }

  return (
    <div className="bg-white">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_20%,rgba(45,109,255,0.08),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(245,159,0,0.08),transparent_20%)]" />
        <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-4 py-16 md:px-6 lg:grid-cols-2 lg:py-20">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-2 text-sm font-semibold text-primary-700">
              내 스택 기반 AI 추천
            </div>
            <div className="space-y-4">
              <h1 className="text-3xl font-bold leading-tight text-slate-950 sm:text-4xl lg:text-5xl">
                내 기술 스택과 커리어 단계에 맞춰
                <br />
                채용공고와 부트캠프를 한 번에.
              </h1>
              <p className="max-w-xl text-lg text-slate-600">
                기술 스택, 커리어 단계, 성장 목표를 입력하면 가장 적합한 채용과 부트캠프를 큐레이션해드려요. 더 이상 흩어진 정보를
                찾느라 시간을 쓰지 마세요.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/login"
                className="rounded-full bg-gradient-to-r from-primary-500 to-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-soft transition hover:shadow-lg hover:shadow-primary-200"
              >
                지금 바로 추천 받기
              </Link>
              <Link
                to="/jobs"
                className="rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-800 transition hover:border-primary-200 hover:text-primary-700"
              >
                채용공고 둘러보기
              </Link>
              <Link
                to="/bootcamps"
                className="rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-800 transition hover:border-primary-200 hover:text-primary-700"
              >
                부트캠프 둘러보기
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-100 bg-white/80 p-4 shadow-soft sm:grid-cols-4">
              <div>
                <p className="text-2xl font-bold text-slate-950">+1,240</p>
                <p className="text-xs text-slate-500">실시간 맞춤 채용</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-950">+180</p>
                <p className="text-xs text-slate-500">부트캠프 과정</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-950">94%</p>
                <p className="text-xs text-slate-500">만족도</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-950">24시간</p>
                <p className="text-xs text-slate-500">업데이트 주기</p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-x-6 top-8 h-full rounded-3xl bg-gradient-to-b from-primary-100/80 to-white blur-2xl" />
            <div className="relative rounded-3xl border border-slate-100 bg-white/90 p-6 shadow-soft">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-primary-700">추천 미리보기</p>
                  <h3 className="text-xl font-bold text-slate-900">내 스택에 맞는 포지션</h3>
                  <p className="text-sm text-slate-500">입력한 정보로 즉시 맞춤 리스트를 생성합니다.</p>
                </div>
                <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">실시간</span>
              </div>

              <div className="mt-6 space-y-3">
                {previewItems.map((item) => (
                  <div
                    key={`${item.title}-${item.company}`}
                    className="flex items-start justify-between rounded-2xl border border-slate-100 bg-slate-50/60 p-4"
                  >
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-primary-700">{item.type}</p>
                      <p className="text-lg font-semibold text-slate-900">{item.title}</p>
                      <p className="text-sm text-slate-600">{item.company}</p>
                      <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                        {item.tag}
                      </div>
                    </div>
                    <div className="flex h-full items-center">
                      <span className="rounded-full bg-primary-600 px-3 py-1 text-xs font-semibold text-white">맞춤</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-100 bg-gradient-to-b from-white to-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-14 md:px-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold text-primary-700">온보딩 2단계</p>
              <h2 className="text-2xl font-bold text-slate-950 sm:text-3xl">간단한 정보만 입력하면 맞춤 추천 시작</h2>
              <p className="mt-2 text-sm text-slate-600">
                기술 스택과 커리어 단계만 선택하면 AI가 바로 큐레이션합니다. 추후 프로필 연동으로 더 정교해집니다.
              </p>
            </div>
            <button
              onClick={() => {
                const params = new URLSearchParams()
                const isCareerLevelOne = selectedCareerLevelId === 1

                // 커리어 레벨 1 사용자는 기술 스택이 필수
                if (isCareerLevelOne && selectedStacks.length === 0) {
                  window.alert('커리어 레벨 1은 기술 스택 키워드를 최소 1개 입력해주세요.')
                  return
                }
                
                // 기술 스택
                if (selectedStacks.length > 0) {
                  selectedStacks.forEach(skill => {
                    params.append('skills', skill)
                  })
                }
                
                // 항목: 커리어 레벨 1은 부트캠프만 강제
                if (isCareerLevelOne) {
                  params.set('source', '부트캠프')
                } else if (selectedSource && selectedSource !== '전체') {
                  params.append('source', selectedSource)
                }
                
                // 커리어 레벨
                if (selectedCareerLevelId) {
                  params.append('careerLevelId', selectedCareerLevelId.toString())
                }
                
                // 경력 구간
                if (selectedExperienceRangeId) {
                  params.append('experienceRangeId', selectedExperienceRangeId.toString())
                }
                
                navigate(`/search?${params.toString()}`)
              }}
              className="inline-flex w-fit items-center justify-center rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-slate-800"
            >
              30초만에 시작하기
            </button>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            {/* STEP 1: 기술 스택 입력 - 수정된 부분 */}
            <StepCard
              step={{
                title: '기술 스택 입력',
                description: '주력 기술을 선택하면 관련 채용과 부트캠프를 먼저 보여드려요.',
              }}
              index={1}
              className="relative overflow-visible"
            >
              <div className="mt-3">
                <div className="flex flex-wrap gap-2">
                  {selectedStacks.map((stack) => (
                    <span
                      key={stack}
                      className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-800 ring-1 ring-inset ring-slate-200"
                    >
                      {stack}
                      <button 
                        onClick={() => toggleStack(stack)}
                        className="ml-2 text-slate-400 hover:text-slate-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  
                  {/* + 선택 버튼 */}
                  <button 
                    onClick={() => setIsSkillSearchOpen(!isSkillSearchOpen)}
                    className="flex items-center gap-1 rounded-full border border-dashed border-primary-300 bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 transition hover:bg-primary-100"
                  >
                    + 스킬 선택
                  </button>
                </div>

                {/* 검색창 UI 팝업 */}
                {isSkillSearchOpen && (
                  <div className="absolute left-0 mt-3 w-full z-10 px-6">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xl ring-1 ring-slate-900/5">
                      {/* 검색 인풋 */}
                        <div className="relative mb-4">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                          <SearchIcon />
                        </div>
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              const q = searchQuery.trim()
                              if (!q) return

                              // 대소문자 구분 없이 기존 스킬이면 해당 스킬로 토글
                              const found = allSkills.find(s => s.toLowerCase() === q.toLowerCase())
                              if (found) {
                                toggleStack(found)
                              } else {
                                if (!selectedStacks.includes(q)) {
                                  setSelectedStacks(prev => [...prev, q])
                                }
                              }
                              setSearchQuery('')
                            }
                          }}
                          className="block w-full rounded-xl border-0 bg-white py-3 pl-10 pr-4 text-slate-900 ring-1 ring-inset ring-slate-200 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6"
                          placeholder="찾으시는 스킬을 입력해주세요"
                          autoFocus
                        />
                      </div>
                      {/* 검색어가 목록에 없으면 직접 추가할 수 있는 버튼 */}
                      {searchQuery.trim() !== '' && !allSkills.some(s => s.toLowerCase() === searchQuery.trim().toLowerCase()) && !selectedStacks.includes(searchQuery.trim()) && (
                        <div className="mb-2">
                          <button
                            onClick={() => {
                              const q = searchQuery.trim()
                              if (!q) return
                              setSelectedStacks(prev => (prev.includes(q) ? prev : [...prev, q]))
                              setSearchQuery('')
                            }}
                            className="rounded-full border px-4 py-2 text-sm transition-colors border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                          >
                            + 추가: "{searchQuery}"
                          </button>
                        </div>
                      )}

                      {/* 스킬 태그 목록 */}
                      <div className="flex max-h-48 flex-wrap gap-2 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
                        {loadingSkills ? (
                          <div className="text-sm text-slate-500">불러오는 중...</div>
                        ) : (
                          allSkills.map((skill) => (
                            <button
                              key={skill}
                              onClick={() => {
                                toggleStack(skill)
                                setSearchQuery('')
                              }}
                              className={`rounded-full border px-4 py-2 text-sm transition-colors ${
                                selectedStacks.includes(skill)
                                  ? 'border-primary-200 bg-primary-50 text-primary-700 font-semibold'
                                  : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                              }`}
                            >
                              {skill}
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                    {/* 백드롭 (외부 클릭 시 닫기용) */}
                    <div 
                      className="fixed inset-0 z-[-1]" 
                      onClick={() => setIsSkillSearchOpen(false)} 
                    />
                  </div>
                )}
              </div>
            </StepCard>

            <StepCard
              step={{
                title: '커리어 단계 선택',
                description: '현재 경력 레벨과 목표를 알려주시면 난이도와 성장 경로에 맞춰 추천합니다.',
              }}
              index={2}
            >
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {/* Source selector */}
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">항목</label>
                  <select
                    value={selectedSource}
                    onChange={(e) => setSelectedSource(e.target.value as '전체' | '채용'|'부트캠프')}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-primary-600"
                  >
                    <option value="전체">전체</option>
                    <option value="채용">채용공고</option>
                    <option value="부트캠프">부트캠프</option>
                  </select>
                </div>

                {/* Career level selector */}
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">커리어 레벨</label>
                  <select
                    value={selectedCareerLevelId ?? ''}
                    onChange={(e) => setSelectedCareerLevelId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-primary-600"
                  >
                    {careerLevels.length === 0 ? (
                      <option value="">불러오는 중...</option>
                    ) : (
                      careerLevels.map((c: any) => {
                        const id = c.id ?? c.CareerLevelID ?? c.careerlevelid
                        const name = c.name ?? c.CareerName ?? c.careername
                        return (
                          <option key={id} value={id}>{name}</option>
                        )
                      })
                    )}
                  </select>
                </div>

                {/* Experience range selector */}
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">경력 구간</label>
                  <select
                    value={selectedExperienceRangeId ?? ''}
                    onChange={(e) => setSelectedExperienceRangeId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-primary-600"
                  >
                    {experienceRanges.length === 0 ? (
                      <option value="">불러오는 중...</option>
                    ) : (
                      experienceRanges.map((r: any) => {
                        const id = r.id ?? r.RangeID ?? r.rangeid
                        const label = r.name ?? r.RangeName ?? r.rangename ?? r.label ?? r.range
                        return (
                          <option key={id} value={id}>{label}</option>
                        )
                      })
                    )}
                  </select>
                </div>
              </div>
            </StepCard>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-100 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-14 md:px-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold text-primary-700">인기 공고 미리보기</p>
              <h2 className="text-2xl font-bold text-slate-950 sm:text-3xl">채용과 부트캠프 인기 공고</h2>
              <p className="mt-2 text-sm text-slate-600">
                인기있는 채용공고와 부트캠프를 한 번에 확인해보세요.
              </p>
            </div>
            <Link
              to="/jobs"
              className="inline-flex w-fit items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-800 transition hover:border-primary-200 hover:text-primary-700"
            >
              전체 보기
            </Link>
          </div>

          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {loadingRecommendations ? (
              <>
                <div className="flex h-56 flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
                  <div className="h-6 w-3/4 animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-full animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200"></div>
                </div>
                <div className="flex h-56 flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
                  <div className="h-6 w-3/4 animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-full animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200"></div>
                </div>
                <div className="flex h-56 flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
                  <div className="h-6 w-3/4 animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-full animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200"></div>
                </div>
                <div className="flex h-56 flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
                  <div className="h-6 w-3/4 animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-full animate-pulse rounded bg-slate-200"></div>
                  <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200"></div>
                </div>
              </>
            ) : (
              recommendations.map((rec, index) => (
                <div
                  key={`${rec.title}-${index}`}
                  className="flex h-56 flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="line-clamp-2 flex-1 text-lg font-bold text-slate-900">{rec.title}</h3>
                    <span className="shrink-0 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                      {index < 2 ? '채용' : '부트캠프'}
                    </span>
                  </div>
                  <p className="line-clamp-3 flex-1 text-sm text-slate-600">{rec.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {rec.tags.map((tag, tagIndex) => (
                      <span
                        key={`${tag}-${tagIndex}`}
                        className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-800 ring-1 ring-slate-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage