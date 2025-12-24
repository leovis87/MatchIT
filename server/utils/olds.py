class Olds:
    def __init__(self):
        pass
    # ========================================================================
    # 클래스 변수
    # Bootcamps DB 조회 시 사용
    # table: jabcategories
    # column: category_name
    # ========================================================================
    CATEGORY_KEYWORDS = {
        'Backend Developer': [
            'backend', '백엔드', 'server', 'api', 'spring', 'django', 'flask',
            'fastapi', 'node.js', 'express', 'nest.js', 'java', 'python server',
            'go server', 'kotlin server', 'restful', 'graphql'
        ],
        'Frontend Developer': [
            'frontend', '프론트엔드', 'react', 'vue', 'angular', 'next.js',
            'javascript', 'typescript', 'html', 'css', 'sass', 'webpack',
            'web developer', '웹 개발'
        ],
        'Full Stack Developer': [
            'full stack', '풀스택', 'fullstack'
        ],
        'AI/ML Engineer': [
            'ai', 'ml', 'machine learning', 'deep learning', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'keras', '딥러닝', '머신러닝', '인공지능',
            'llm', 'gpt', 'model', 'data scientist', 'deep_learning'
        ],
        'Data Engineer': [
            'data engineer', '데이터 엔지니어', 'etl', 'data pipeline', 'airflow',
            'spark', 'hadoop', 'kafka', 'data warehouse', 'bigquery', '데이터분석'
        ],
        'Data Analyst': [
            'data analyst', '데이터 분석', 'bi', 'tableau', 'power bi', 'sql',
            'data visualization', '데이터 시각화', '데이터분석'
        ],
        'DevOps Engineer': [
            'devops', 'sre', 'infrastructure', '인프라', 'kubernetes', 'docker',
            'ci/cd', 'jenkins', 'terraform', 'ansible', 'aws', 'gcp', 'azure',
            'cloud engineer', 'cloud'
        ],
        'Mobile Developer': [
            'mobile', 'android', 'ios', 'react native', 'flutter', 'swift',
            'kotlin', '모바일', 'app developer'
        ],
        'Security Engineer': [
            'security', '보안', 'infosec', '정보보안', 'penetration', 'vulnerability',
            '보안솔루션', 'firewall', 'ids', 'ips'
        ],
        'QA Engineer': [
            'qa', 'quality assurance', 'test', '테스트', 'automation test',
            'selenium', 'cypress'
        ],
        'Product Manager': [
            'product manager', 'pm', 'po', 'product owner', '기획', '서비스 기획'
        ],
        'UI/UX Designer': [
            'ui', 'ux', 'designer', '디자이너', 'figma', 'sketch', 'prototype'
        ],
        'Database Engineer': [
            'dba', 'database', '데이터베이스', 'postgresql', 'mysql', 'oracle',
            'mssql', 'mongodb', 'db admin'
        ],
        'Blockchain Developer': [
            'blockchain', '블록체인', 'solidity', 'ethereum', 'web3', 'defi', 'nft'
        ],
        'Game Developer': [
            'game', '게임', 'unity', 'unreal', 'c++', 'graphics'
        ],
    }

    # ========================================================================
    # category_name: skills 매칭 함수
    # table: jabcategories
    # column: category_name
    # ========================================================================
    def match_category(self,
                       query: str) -> str:
        """
        사용자 query를 CATEGORY_KEYWORDS 기반으로 카테고리 매칭
        """
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in query.lower():
                    return category
        return None

# 추천 방식을 기존 LLM -> embedding vector 유사도로 변경
#     def score_with_exaone(self,
#                           query: str,
#                           education_content: str):
#         """
#         EXAONE 모델을 호출해 query와 education_content의 매칭 점수를 0~100으로 평가
#         """
#         prompt = f"""[|system|]너는 분석가야.
# 사용자 입력: "{query}"
# 부트캠프 교육 내용: "{education_content}"

# 위 사용자 입력과 부트캠프 교육 내용이 얼마나 잘 맞는지 0~100 사이 점수로 평가해.
# 그리고 그 이유를 1-2문장으로 설명해 줘.

# 출력 형식:
# 점수: <숫자만>
# 이유: <30자 이내 한 문장>[|endofturn|]
# [|assistant|]"""
#         # 1. 문자열(query) -> tokenize -> tensor 변환
#         inputs = self.tokenizer(prompt, return_tensors = 'pt').to(self.model.device)

#         # 2. 모델 generate 호출 (텐서 반환)
#         response = self.model.generate(**inputs, # 토큰화된 텐서 전달
#                                        max_new_tokens = 100, # 새로 생성할 토큰 수 제한
#                                        num_return_sequences = 1, # 생성할 응답 개수
#                                        do_sample = True, # 샘플링 활성화
#                                        temperature = 0.7)  # 샘플링 온도 (창의성 조절) // 0이면 계속 같은 대답
        
#         # 3. 디코딩 (문자열 반환)
#         decoded = self.tokenizer.decode(response[0], skip_special_tokens = False)

#         # 4. 디코딩 -> [|assistant|] 이후 텍스트만 추출
#         if "[|assistant|]" in decoded:
#             decoded = decoded.split("[|assistant|]")[-1]

#         # 5. [|endofturn|] 제거
#         if "[|endofturn|]" in decoded:
#             decoded = decoded.split("[|endofturn|]")[0]

#         # 6. Ai의 점수 및 추천 이유 파싱
#         score, reason = 0, ''

#         for line in decoded.splitlines():  # splitlines: 문자열 사용
#             if line.startswith("점수:"):
#                 # 숫자만 추출 (정규식으로 명시적 지정)
#                 match = re.search(r'\d+', line)

#                 if match:
#                     score = int(match.group())
#             elif line.startswith("이유:"):
#                 reason = line.replace("이유:", "").strip()
        
#         return score, reason

    # def recommend_bootcamps(self,
    #                         query: str,
    #                         db: Session,
    #                         limit: int = 3):
    #     """
    #     사용자 query 기반으로 부트캠프 추천 (카테고리 매칭 + EXAONE 점수 + 랜덤 샘플링)
    #     """
    #     # 1. 카테고리 추출
    #     category = self.match_category(query)

    #     # 2. DB 검색
    #     bootcamps = self.search_bootcamps(db, category_name = category, limit = 10)
    #     if not bootcamps:
    #         return []

    #     # 3. AI 점수 + 추천 이유 생성
    #     scored = []
    #     for bc in bootcamps:
    #         score, reason = self.score_with_exaone(query, bc.get('educationcontent', ''))
    #         scored.append((bc, score, reason))

    #     # 4. 점수 높은 순으로 정렬
    #     scored.sort(key = lambda x: x[1], reverse = True)

    #     # 5. 상위 5개 중 랜덤으로 limit개 뽑기
    #     top_candidates = scored[:5]

    #     # recommended: Tutle #[(bc_dict, score, reason), ...]
    #     recommended = random.sample(top_candidates, k = min(limit, len(top_candidates)))
        
    #     # card 형식으로 변환
    #     cards = []
    #     for bc, score, reason in recommended:
    #         name_display = bc.get('name', '부트캠프')
    #         if bc.get('url'):
    #             name_display = f"[{bc.get('name', '부트캠프')}]({bc['url']})"
    #         card = {
    #             'name': name_display,                  # MarkDown형식 link
    #             'subtitle': f'점수: {score}',          # 점수
    #             'description': f'추천이유: {reason}',  # 추천 이유
    #             'extra': {                            # 부가 항목 모음
    #                 'category': bc.get('category_name', ''),
    #                 'link': bc.get('url', ''), # 원본 url 그대로 저장
    #                 'cost_type': bc.get('cost_type', ''), # 국비 | 본인부담
    #                 'institute': bc.get('institute', ''), # 기관명   
    #                 'online_offline': bc.get('online_offline'), # 온라인 | 오프라인
    #                 'educationcontent': bc.get('educationcontent'), # 수업내용
    #                 'location': bc.get('location', ''), # 주소
    #             }
    #         }
    #         cards.append(card)

    #     return cards
    
    # 'name': bc.Title or '부트캠프명 없음',
    # 'institute': bc.InstituteName or '기관명 없음',
    # 'cost_type': bc.CostSupportType or '본인부담',
    # 'location': bc.Location or '온라인',
    # 'online_offline': bc.OnlineOffline or '온라인',
    # 'url': bc.DetailUrl or '',
    # 'educationcontent': bc.EducationContent or '',
    # 'category_name': bc.job_category.CategoryName if bc.job_category else ''

    # 출력 예: List[Tuple]
    # [
    #     {
    #         "name": "[Django 백엔드 과정](https://example.com/django-bootcamp)",
    #         "subtitle": "점수: 85",
    #         "description": "사용자가 Django를 배우고 싶다고 했기 때문에 이 과정이 적합합니다.",
    #         "extra": {
    #         "category": "Backend Developer",
    #         "link": "https://example.com/django-bootcamp"
    #         }
    #     },
    # ]


    # vector 검색으로 대체
    # def search_jobs(self,
    #                 db: Session,
    #                 profile: Dict,
    #                 limit: int = 3) -> List[Dict]:
    #     from src.models import JobPost, Skill
    #     query = db.query(JobPost).filter(JobPost.IsActive == True)
        
    #     if profile['skills']:
    #         query = query.join(JobPost.skills).filter(
    #             or_(*[Skill.SkillName.ilike(f"%{s}%") for s in profile['skills']])
    #         )
    #     if profile['location']:
    #         query = query.filter(JobPost.Location.ilike(f"%{profile['location']}%"))
    #     if profile['experience']:
    #         query = query.filter(JobPost.ExperienceRequirement.ilike(f"%{profile['experience']}%"))
        
    #     results = query.limit(limit).all()
    #     return [{
    #         'company': job.CompanyName or '회사명 미공개',
    #         'title': job.Title or '직무명 없음',
    #         'location': job.Location or '위치 미정',
    #         'experience': job.ExperienceRequirement or '무관',
    #         'salary': job.Salary or '협의',
    #         'skills': [s.SkillName for s in job.skills] if job.skills else [],
    #         'url': job.Url or '',
    #     } for job in results]

    

    # vector 검색으로 대체
    # def search_bootcamps(self,
    #                      db: Session,
    #                      missing_skills: List[str] = None,
    #                      category_name: str = None,
    #                      limit: int = 2) -> List[Dict]:
    #     from src.models import BootcampPost, JobCategory
    #     query = db.query(BootcampPost)
        
    #     # 사용자의 부족한 스킬 기반 필터링
    #     if missing_skills:
    #         filters = [BootcampPost.EducationContent.ilike(f"%{s}%") for s in missing_skills]
    #         if filters:
    #             query = query.filter(or_(*filters))
        
    #     # 카테고리 이름 기반 필터링 (JobCategory와 조인)
    #     if category_name:
    #         query = query.join(BootcampPost.job_category).filter(JobCategory.CategoryName == category_name)

    #     # 정렬: 국비지원 우선 -> 조회수 순
    #     query = query.order_by(BootcampPost.CostSupportType.desc(), BootcampPost.ViewCount.desc())
    #     results = query.limit(limit).all()

    #     # Dict 형태로 변환
    #     return [{
    #         'name': bc.Title or '부트캠프명 없음',
    #         'institute': bc.InstituteName or '기관명 없음',
    #         'cost_type': bc.CostSupportType or '본인부담',
    #         'location': bc.Location or '온라인',
    #         'online_offline': bc.OnlineOffline or '온라인',
    #         'url': bc.DetailUrl or '',
    #         'educationcontent': bc.EducationContent or '',
    #         'category_name': bc.job_category.CategoryName if bc.job_category else ''
    #     } for bc in results]
