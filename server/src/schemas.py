from enum import Enum
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy import Column, Enum as SQLEnum
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Tuple, Union, Literal, Optional

'''
pipline
사용자 → FastAPI → Pydantic 검증 → 비즈니스 로직 → SQLAlchemy → DB
         (API)    (1차 방어)      (처리)          (2차 방어)   (저장)

각 Schema의 column에 입력되는 type을 지정

예시:
    pydantic: 1차관문 ->  DB까지 가지전에 걸러줌
    sql: 2차관문 -> 데이터 무결성 최종 보장

    datetime.now() = 사진 한 장 찍어서 복사
    default_factory=datetime.now = 필요할 때마다 새로 찍기
'''

##################################################################################
# Enums
##################################################################################
class Provider_sns(str, Enum):
    KAKAO = 'kakao'
    NAVER = 'naver'
    GOOGLE = 'google'

class Provider_job(str, Enum):
    REMEMBER = 'remember'
    WANTED = 'wanted'

class Post_type(str, Enum):
    JOB = 'job'
    BOOTCAMP = 'bootcamp'

class Online_offline(str, Enum):
    ONLINE = '온라인'
    OFFLINE = '오프라인'
    MIX = '혼합형'

class Cost_support_type(str, Enum):
    PAY_K = '국비지원'
    PAY_SELF = '본인부담'


##################################################################################
# Chatbot
##################################################################################
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    status: str = 'success'

##################################################################################
# === kakao api login ===
##################################################################################
# === 1. kakao login requier ===
class SocialLoginRequest(BaseModel):
    '''
    front가 보내는 kakao token
    '''
    provider: Provider_sns
    access_token: str = Field(min_length = 1)

# === 2. kakao API response (내부용) ===
class KakaoUserInfo(BaseModel):
    '''
    카카오 API에서 받은 사용자 정보
    '''
    id: int  # 카카오 고유 ID
    kakao_account: dict  # 이메일 등 포함
    # properties: dict  # 닉네임 등

# === 3. server response ===
class LoginResponse(BaseModel):
    '''
    로그인 성공 후 반환
    '''
    access_token: str  # 우리 서버의 JWT
    token_type: str = "bearer"
    user: dict  # 사용자 정보

# === 4. user create (/auth/register) ===
class UserCreateFromSocial(BaseModel):
    '''
    소셜 로그인으로 자동 생성
    '''
    name: str
    email: EmailStr
    provider: Provider_sns
    provider_user_id: str  # 카카오 ID
    # Password 없음!


##################################################################################
# === Admin 관련 ===
##################################################################################
class UserOut(BaseModel):
    userid: int
    email: str
    name: Optional[str]
    role: int  # 1 for user, 2 for admin

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    roleid: int  # 1 for user, 2 for admin


class JobPostOut(BaseModel):
    jobid: int
    jobtitle: str
    company: Optional[str]
    jobdescription: Optional[str]

    class Config:
        from_attributes = True

class JobPostUpdate(BaseModel):
    jobtitle: Optional[str] = None
    jobdescription: Optional[str] = None


class BootcampOut(BaseModel):
    bootcampid: int
    bootcampname: str
    institution: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BootcampUpdate(BaseModel):
    bootcampname: Optional[str] = None
    institution: Optional[str] = None
    description: Optional[str] = None


##################################################################################
# === POST ===
##################################################################################
class DesiredJobsPost(BaseModel):
    '''
    endpoint:
        /users/{user_id}/desiredjobs

    params:
        desiredjob_id

    description:
        특정 유저가 원하는 희망 직무를 설정/등록합니다.
    '''
    desiredjob_id: int

class UserSkillPost(BaseModel):
    '''
    endpoint:
        /users/{user_id}/skills

    params:
        skill_id

    description:
        특정 유저의 스킬 목록에 새로운 스킬(skill_id)을 추가/등록합니다.
    '''
    skill_id: int

class UserScrapPost(BaseModel):
    '''
    endpoint:
        /users/{user_id}/scraps

    params:
        post_type(Job, Bootcamp),
        target_id

    description:
        특정 유저의 스크랩 목록에 새로운 항목을 추가합니다.
    '''
    post_type: Post_type
    target_id: int

class JobPost(BaseModel):
    '''
    endpoint:
        /jobs

    params:
        provider, title, company_name,
        ...
    
    description:
        관리자가 새로운 구직공고 정보를 등록.
        구직공고명, 회사명, 카테고리, 상세 내용 등을 포함하여 생성.

    주의:
        실데이터에는 일부 필드가 NULL/빈값일 수 있으므로 Optional로 허용한다.
    '''
    provider: Provider_job
    title: Optional[str] = Field(None, max_length = 500)
    company_name: Optional[str] = Field(None, max_length = 500)
    job_category: Optional[str] = Field(None, max_length = 500)
    employment_type: Optional[str] = Field(None, max_length = 500)
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    location: Optional[str] = None
    main_tasks: Optional[str] = Field(None, max_length = 10000)
    qualifications: Optional[str] = Field(None, max_length = 10000)
    preferences: Optional[str] = Field(None, max_length = 10000)
    benefits: Optional[str] = Field(None, max_length = 10000)
    process: Optional[str] = Field(None, max_length = 10000)
    salary: Optional[str] = None
    posted_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    # 실데이터에 스킴 없는 문자열이 존재할 수 있어 문자열로 완화
    url: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: datetime = Field(default_factory = datetime.now)
    updated_at: datetime = Field(default_factory = datetime.now)

class JobPostCreate(BaseModel): 
    PlatformID: int 
    Title: str = Field(max_length=255)
    CompanyName: str = Field(max_length=255)
    JobCategoryID: int
    EmploymentType: Optional[str] = Field(default=None, max_length=50)
    ExperienceRequirement: str = Field(max_length=10)
    MinExperienceYears: Optional[int] = 0 
    EducationRequirement: Optional[str] = Field(default=None, max_length=50)
    Location: Optional[str] = Field(default=None, max_length=255)
    MainTasks: Optional[str] = None 
    Qualifications: Optional[str] = None 
    Preferences: Optional[str] = None 
    Benefits: Optional[str] = None 
    Process: Optional[str] = None 
    Salary: Optional[str] = Field(default=None, max_length=100)
    PostedDate: Optional[date] = None 
    CloseDate: Optional[date] = None 
    Url: Optional[str] = None 
    IsActive: bool = True
    SkillIDs: Optional[List[int]] = None 


class JobPostUpdate(BaseModel):
    PlatformID: Optional[int] = None 
    Title: Optional[str] = Field(default=None, max_length=255)
    CompanyName: Optional[str] = Field(default=None, max_length=255)
    JobCategoryID: Optional[int] = None
    EmploymentType: Optional[str] = Field(default=None, max_length=50)
    ExperienceRequirement: Optional[str] = Field(default=None, max_length=10)
    MinExperienceYears: Optional[int] = None
    EducationRequirement: Optional[str] = Field(default=None, max_length=50)
    Location: Optional[str] = Field(default=None, max_length=255)
    MainTasks: Optional[str] = None 
    Qualifications: Optional[str] = None
    Preferences: Optional[str] = None
    Benefits: Optional[str] = None
    Process: Optional[str] = None
    Salary: Optional[str] = Field(default=None, max_length=100)
    PostedDate: Optional[date] = None
    CloseDate: Optional[date] = None
    Url: Optional[str] = None
    IsActive: Optional[bool] = None
    SkillIDs: Optional[List[int]] = None


class JobPostResponse(BaseModel):
    PostID: int
    PlatformID: int
    Title: str
    CompanyName: str
    JobCategoryID: int
    EmploymentType: Optional[str]
    ExperienceRequirement: str
    MinExperienceYears: int
    EducationRequirement: Optional[str]
    Location: Optional[str]
    MainTasks: Optional[str]
    Qualifications: Optional[str] 
    Preferences: Optional[str]
    Benefits: Optional[str]
    Process: Optional[str]
    Salary: Optional[str]
    PostedDate: Optional[date]
    CloseDate: Optional[date]
    ViewCount: int
    Url: Optional[str]
    IsActive: bool
    CreatedAt: datetime
    UpdatedAt: datetime
    Skills: List[str] = [] 

    class Config:
        from_attributes = True


class PaginatedJobPostResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[JobPostResponse]
class BootcampPost(BaseModel):
    '''
    endpoint:
        /bootcamps

    params:
        title, institute_name,
        job_category_id, location
        ...

    description:
        관리자가 새로운 부트캠프 정보를 등록.
        부트캠프명, 운영 기관, 카테고리, 상세 내용 등을 포함하여 생성.

    주의:
        실데이터 필드가 비어 있을 수 있어 Optional 허용.
    '''
    title: str = Field(max_length = 500)
    institute_name: str
    job_category_id: int
    location: Optional[str] = None
    online_offline: Online_offline = Online_offline.ONLINE
    cost_support_type: Cost_support_type = Cost_support_type.PAY_SELF
    education_content: Optional[str] = Field(None, max_length = 10000)
    qualification: Optional[str] = Field(None, max_length = 10000)
    benefits: Optional[str] = Field(None, max_length = 10000)
    start_date: Optional[datetime] = None
    registration_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    detail_url: Optional[str] = None

class BootcampCreate(BaseModel):
    Title: str
    InstituteName: str
    JobCategoryID: int
    Location: Optional[str] = None
    OnlineOffline: str = "온라인"
    CostSupportType: str = "본인부담"
    EducationContent: Optional[str] = None
    Qualification: Optional[str] = None
    Benefits: Optional[str] = None
    StartDate: Optional[datetime] = None
    RegistrationDate: Optional[datetime] = None
    CloseDate: Optional[datetime] = None
    DetailUrl: Optional[str] = None

class BootcampResponse(BaseModel):
    BootcampID: int
    Title: str
    InstituteName: str
    JobCategoryID: int
    CategoryName: Optional[str]  # 추가
    Location: Optional[str]
    OnlineOffline: str
    CostSupportType: str
    EducationContent: Optional[str]
    Qualification: Optional[str]
    Benefits: Optional[str]
    StartDate: Optional[datetime]
    RegistrationDate: Optional[datetime]
    CloseDate: Optional[datetime]
    DetailUrl: Optional[str]
    ViewCount: int
    CreatedAt: datetime
    UpdatedAt: datetime

class BootcampDetailResponse(BaseModel):
    BootcampID: int
    Title: str
    InstituteName: str
    JobCategoryID: int
    Location: Optional[str]
    OnlineOffline: str
    CostSupportType: str
    EducationContent: Optional[str]
    Qualification: Optional[str]
    Benefits: Optional[str]
    StartDate: Optional[datetime]
    RegistrationDate: Optional[datetime]
    CloseDate: Optional[datetime]
    DetailUrl: Optional[str]
    ViewCount: int
    CreatedAt: datetime
    UpdatedAt: datetime


##################################################################################
# === GET ===
##################################################################################
class UserGet(BaseModel):
    '''
    endpoint:
        /users/{user_id}

    params:
        user_id
    
    description:
        "관리자" 권한으로 특정 사용자의 정보를 조회합니다.
    '''
    user_id: int

# 아이디어 있으시면 부탁드립니다.
# class MyProfileGet(BaseModel):
#     '''
#     endpoint:
#         /users/me

#     params:
#         JWT
    
#     description:
#         인증된 사용자가 자신의 프로필 정보를 조회합니다.
#     '''
#     JWT: # here... how??

class JobCategoryGet(BaseModel):
    '''
    endpoint:
        /jobcategories/{category_id}

    params:
        category_id

    description:
        지정한 카테고리 ID로 직무 카테고리의 상세 정보를 조회.
        카테고리명, 설명, 상위/하위 구조 등이 반환.
    '''
    category_id: int

class JobCategoriesGet(BaseModel):
    '''
    endpoint:
        /jobcategories

    params:
        parent_id(optional)

    description:
        모든 직무 카테고리를 트리 구조(계층적)로 조회.
        필요 시, parent_id 파라미터로 특정 루트/상위 카테고리부터
        하위 카테고리까지 탐색이 가능합니다.
    '''
    parent_id: Optional[int] = None

# 추후 제한 사항 추가 시, 추가 가능
# class AllPlatformGet(BaseModel):
#     '''
#     endpoint:
#         /platforms

#     params:
#         None

#     description:
#         등록된 모든 플랫폼(서비스, 웹사이트 등)의 리스트를 조회.
#         각 플랫폼의 이름, 설명, 제공 서비스가 포함.
#     '''

class BootcampGet(BaseModel):
    '''
    endpoint:
        /bootcamps{bootcamp_id}

    params:
        bootcamp_id
        ...

    description:
        사용자가 특정 부트캠프의 상세 정보를 확인.
        교육 과정, 일정, 지원 자격 등이 포함될 수 있음.
    '''
    bootcamp_id: int

class SortBootcampGet(BaseModel):
    '''
    endpoint:
        /bootcamps

    params:
        page, size, keyword,
        skill, category_id

    description:
        여러 조건(페이지네이션, 키워드, 스킬, 카테고리 등)으로
        전체 부트캠프 리스트를 조회. 검색 및 필터링 기능이 포함.
    '''
    page: Optional[int] = None
    # size: ??
    keyword: Optional[str] = None
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None
    category_id: Optional[int] = None


class CareerLevelPost(BaseModel):
    '''
    endpoint:
        /careerlevels

    params:
        career_name

    description:
        새로운 커리어 레벨을 등록합니다.
    '''
    career_name: str = Field(max_length=50)


class CareerLevelGet(BaseModel):
    '''
    endpoint:
        /careerlevels/{career_level_id}

    params:
        career_level_id

    description:
        커리어 레벨의 상세 정보를 조회합니다. (ID, 이름)
    '''
    career_level_id: int
    career_name: str
    category_name: Optional[str] = None

class PaginatedBootcampResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[BootcampResponse]

class UserScrapGet(BaseModel):
    '''
    endpoint:
        /users/{user_id}/scraps

    params:
        post_type,
        job_post_id, bootcamp_post_id

    description:
        특정 유저가 스크랩한 항목(직무/부트캠프)의 목록을 조회.
        filter를 통해, 직무 또는 부트캠프 별로 필터링.
    '''
    post_type: Optional[Post_type] = None
    job_post_id: Optional[int] = None
    bootcamp_post_id: Optional[int] = None

class SocialLoginGet(BaseModel):
    '''
    endpoint:
        /auth/social

    params:
        provider,
        provider_user_id,
        email(optional)

    description:
        소셜 로그인을 시도하거나, 기존 계정에 새로운 소셜 계정을 연결.
        provider, 소셜 서비스에서의 유저 ID(provider_user_id) 및
        이메일 정보 사용.
    '''
    provider: Provider_sns
    provider_user_id: str
    email: Optional[EmailStr] = None

class AllSocialLoginsGet(BaseModel):
    '''
    endpoint:
        /users/{user_id}/socials

    params:
        user_id

    description:
        특정 유저(user_id) 계정에 현재 연결되어 있는 소셜 계정들의 목록을 조회.
    '''
    user_id: str

class NotificationsGet(BaseModel):
    '''
    endpoint:
        /users/{user_id}/notifications

    params:
        user_id
    
    description:
        특정 유저(user_id)의 현재 알림 설정 상태를 조회.
    '''
    user_id: str

# 추후 제한 사항 추가 시, 추가 가능
# class AllDesiredJobsGet(BaseModel):
#     '''
#     endpoint:
#         /desiredjobs/

#     params:
#         None

#     description:
#         시스템에 등록된 전체 희망 직무의 목록을 조회. (로그인 불필요)
#     '''
    # desired_job_id: int
    # job_name: str

# 추후 제한 사항 추가 시, 추가 가능
# class Skill(BaseModel):
#     '''
#     endpoint:
#         /desiredjobs/

#     params:
#         None

#     description:
#         시스템에 등록된 전체 스킬의 목록을 조회. (로그인 불필요)
#     '''
#     SkillID: int
#     SkillName: str

##################################################################################
# === PUT ===
##################################################################################
class NotificationPut(BaseModel):
    '''
    endpoint:
        /users/{user_id}/notifications

    params:
        user_id, is_enabled,
        notification_type, notification_time

    description:
        특정 유저(user_id)의 알림 설정 값을 업데이트합니다.
        알림의 종류(notification_type), 활성화 여부(is_enabled),
        알림 시간(notification_time) 등의 정보를 수정할 수 있습니다.
    '''
    user_id: int
    is_enabled: bool = True
    notification_type: str
    notification_time: str

class BootcampUpdate(BaseModel):
    Title: Optional[str] = None
    InstituteName: Optional[str] = None
    JobCategoryID: Optional[int] = None
    Location: Optional[str] = None
    OnlineOffline: Optional[str] = None
    CostSupportType: Optional[str] = None
    EducationContent: Optional[str] = None
    Qualification: Optional[str] = None
    Benefits: Optional[str] = None
    StartDate: Optional[datetime] = None
    RegistrationDate: Optional[datetime] = None
    CloseDate: Optional[datetime] = None
    DetailUrl: Optional[str] = None
    ViewCount: Optional[int] = None