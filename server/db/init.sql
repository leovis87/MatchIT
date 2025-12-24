-- TimeZone 설정 (Asia/Seoul)
ALTER DATABASE matchit_db SET TIMEZONE TO 'Asia/SEOUL';

-- pgvector extension: Vector type for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS test_result (
    keyword     varchar(30) not null constraint test_result_tmp_pkey1 primary key,
    embedding   vector(256) not null,
    modified_at timestamp   not null
);
CREATE INDEX IF NOT EXISTS idx__test_result__embedding
    ON test_result USING hnsw (embedding vector_cosine_ops);

-- 경력 레벨
CREATE TABLE CareerLevels (
    CareerLevelID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CareerName VARCHAR(50) UNIQUE NOT NULL
);

-- 유저
CREATE TABLE Users (
    UserID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name VARCHAR(100),
    Email VARCHAR(255) UNIQUE NOT NULL,
    RoleID INT NOT NULL DEFAULT 1,  -- 1 = user
    CareerLevelID INT,
    RangeID INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role
        FOREIGN KEY (RoleID) REFERENCES Roles(RoleID),
    CONSTRAINT fk_users_careerlevel
        FOREIGN KEY (CareerLevelID) REFERENCES CareerLevels(CareerLevelID),
    CONSTRAINT fk_users_experienceranges
        FOREIGN KEY (RangeID) REFERENCES ExperienceRanges(RangeID)
);

-- UpdatedAt 자동 갱신 트리거(옵션: MySQL의 ON UPDATE CURRENT_TIMESTAMP 대체용)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW."updatedat" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_set_updated_at
BEFORE UPDATE ON Users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- 소셜 로그인 (ENUM → CHECK로 처리)
CREATE TABLE SocialLogins (
    SocialLoginID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    UserID INT NOT NULL,
    Provider VARCHAR(20) NOT NULL,
    ProviderUserID VARCHAR(255) NOT NULL,
    LinkedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UnlinkedAt TIMESTAMP NULL,
    CONSTRAINT uq_sociallogins_user_provider UNIQUE (UserID, Provider),
    CONSTRAINT chk_sociallogins_provider
        CHECK (Provider IN ('Kakao', 'Naver', 'Google')),
    CONSTRAINT fk_sociallogins_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- 희망 직무
CREATE TABLE DesiredJobs (
    DesiredJobID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    JobName VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE UserDesiredJobs (
    UserID INT NOT NULL,
    DesiredJobID INT NOT NULL,
    PRIMARY KEY (UserID, DesiredJobID),
    CONSTRAINT fk_userdesiredjobs_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
    CONSTRAINT fk_userdesiredjobs_desiredjob
        FOREIGN KEY (DesiredJobID) REFERENCES DesiredJobs(DesiredJobID)
);

-- 스킬
CREATE TABLE Skills (
    SkillID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    SkillName VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE UserSkills (
    UserID INT NOT NULL,
    SkillID INT NOT NULL,
    PRIMARY KEY (UserID, SkillID),
    CONSTRAINT fk_userskills_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
    CONSTRAINT fk_userskills_skill
        FOREIGN KEY (SkillID) REFERENCES Skills(SkillID)
);

-- 알림 설정
CREATE TABLE UserNotificationSettings (
    UserNotificationID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    UserID INT NOT NULL,
    NotificationType VARCHAR(100),
    IsEnabled BOOLEAN DEFAULT TRUE,
    NotificationTime VARCHAR(50),
    CONSTRAINT fk_usernotifications_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- 플랫폼
CREATE TABLE Platforms (
    PlatformID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    PlatformName VARCHAR(100) UNIQUE NOT NULL
);

-- 직무 카테고리 (셀프 FK)
CREATE TABLE JobCategories (
    CategoryID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL,
    ParentCategoryID INT NULL,
    Depth SMALLINT NOT NULL DEFAULT 1,
    CONSTRAINT fk_jobcategories_parent
        FOREIGN KEY (ParentCategoryID) REFERENCES JobCategories(CategoryID)
);

-- 채용 공고
CREATE TABLE JobPosts (
    PostID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    PlatformID INT NOT NULL,
    Title VARCHAR(255),
    CompanyName VARCHAR(255),
    JobCategoryID INT NOT NULL,
    EmploymentType VARCHAR(50),
    ExperienceRequirement VARCHAR(10) NOT NULL,
    MinExperienceYears INT DEFAULT 0,
    EducationRequirement VARCHAR(50),
    Location VARCHAR(255),
    MainTasks TEXT,
    Qualifications TEXT,
    Preferences TEXT,
    Benefits TEXT,
    Process TEXT,
    Salary VARCHAR(100),
    PostedDate DATE,
    CloseDate DATE,
    ViewCount INT DEFAULT 0,
    Url VARCHAR(500),
    Embeded VECTOR(768),
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_jobposts_experience_requirement
        CHECK (ExperienceRequirement IN ('신입', '경력')),
    CONSTRAINT fk_jobposts_platform
        FOREIGN KEY (PlatformID) REFERENCES Platforms(PlatformID),
    CONSTRAINT fk_jobposts_jobcategory
        FOREIGN KEY (JobCategoryID) REFERENCES JobCategories(CategoryID)
);

-- UpdatedAt 트리거 (JobPosts)
CREATE TRIGGER trg_jobposts_set_updated_at
BEFORE UPDATE ON JobPosts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- 채용 공고 스킬
CREATE TABLE JobPostSkills (
    PostID INT NOT NULL,
    SkillID INT NOT NULL,
    PRIMARY KEY (PostID, SkillID),
    CONSTRAINT fk_jobpostskills_post
        FOREIGN KEY (PostID) REFERENCES JobPosts(PostID),
    CONSTRAINT fk_jobpostskills_skill
        FOREIGN KEY (SkillID) REFERENCES Skills(SkillID)
);

-- 부트캠프 공고
CREATE TABLE BootcampPosts (
    BootcampID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    InstituteName VARCHAR(255) NOT NULL,
    JobCategoryID INT NOT NULL,
    Location VARCHAR(255),
    OnlineOffline VARCHAR(10) DEFAULT '온라인',
    CostSupportType VARCHAR(10) DEFAULT '본인부담',
    EducationContent TEXT,
    Qualification TEXT,
    Benefits TEXT,
    StartDate DATE,
    RegistrationDate DATE,
    CloseDate DATE,
    DetailUrl VARCHAR(500),
    Embeded VECTOR(768),
    ViewCount INT DEFAULT 0,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_bootcampposts_onlineoffline
        CHECK (OnlineOffline IN ('온라인', '오프라인', '혼합형')),
    CONSTRAINT chk_bootcampposts_costsupporttype
        CHECK (CostSupportType IN ('국비지원', '본인부담')),
    CONSTRAINT fk_bootcampposts_jobcategory
        FOREIGN KEY (JobCategoryID) REFERENCES JobCategories(CategoryID)
);

-- 스크랩 (PostType ENUM → CHECK, COALESCE UNIQUE → 부분 인덱스로 대체 추천)
CREATE TABLE UserScraps (
    ScrapID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    UserID INT NOT NULL,
    PostType VARCHAR(20) NOT NULL,
    JobPostID INT NULL,
    BootcampPostID INT NULL,
    ScrappedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_userscraps_posttype
        CHECK (PostType IN ('Job', 'Bootcamp')),
    CONSTRAINT fk_userscraps_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
    CONSTRAINT fk_userscraps_jobpost
        FOREIGN KEY (JobPostID) REFERENCES JobPosts(PostID),
    CONSTRAINT fk_userscraps_bootcamppost
        FOREIGN KEY (BootcampPostID) REFERENCES BootcampPosts(BootcampID),
    CONSTRAINT chk_userscraps_only_one_ref
        CHECK (
            (PostType = 'Job' AND JobPostID IS NOT NULL AND BootcampPostID IS NULL) OR
            (PostType = 'Bootcamp' AND BootcampPostID IS NOT NULL AND JobPostID IS NULL)
        )
);

-- UserScraps의 "User별, 타입별 한 번만" 제약을 위해 부분 유니크 인덱스 사용
CREATE UNIQUE INDEX uq_userscraps_job
    ON UserScraps (UserID, JobPostID)
    WHERE PostType = 'Job';

CREATE UNIQUE INDEX uq_userscraps_bootcamp
    ON UserScraps (UserID, BootcampPostID)
    WHERE PostType = 'Bootcamp';

-- Login Session DB 저장
CREATE TABLE UserSessions (
    SessionID UUID PRIMARY KEY,
    UserID INT NOT NULL REFERENCES Users(UserID),
    AccessToken VARCHAR(255) NOT NULL,
    RefreshToken VARCHAR(255),
    ExpiresAt TIMESTAMP NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 연차 구간을 위한 별도 테이블 추가
CREATE TABLE ExperienceRanges (
    RangeID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    RangeName VARCHAR(20) UNIQUE NOT NULL,  -- '1년 미만', '1~3년', '3~5년' 등
    MinYears INT DEFAULT 0,
    MaxYears INT NULL  -- NULL이면 상한 없음
);

-- CareerLevels에 RangeID 추가
ALTER TABLE CareerLevels ADD COLUMN ExperienceRangeID INT REFERENCES ExperienceRanges(RangeID);


-- 역할 (관리자/유저)
CREATE TABLE Roles (
    RoleID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    RoleName VARCHAR(50) UNIQUE NOT NULL
);