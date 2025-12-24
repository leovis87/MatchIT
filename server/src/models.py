from src.database import Base
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Text,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, func
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Base = declarative_base()
KST = timezone(timedelta(hours = 9))

# -------------------------------------------------------
# CareerLevels
# -------------------------------------------------------
class CareerLevel(Base):
    __tablename__ = "careerlevels"

    CareerLevelID = Column("careerlevelid", Integer, primary_key=True, autoincrement=True)
    CareerName = Column("careername", String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="career_level")


# -------------------------------------------------------
# ExperienceRanges
# -------------------------------------------------------
class ExperienceRange(Base):
    __tablename__ = "experienceranges"

    RangeID = Column("rangeid", Integer, primary_key=True, autoincrement=True)
    RangeName = Column("rangename", String(100), nullable=False)
    MinYears = Column("minyears", Integer, nullable=True)
    MaxYears = Column("maxyears", Integer, nullable=True)

    users = relationship("User", back_populates="experience_range")
    def to_dict(self):
        return {
            "id": self.RangeID,
            "name": self.RangeName,
            "min_years": self.MinYears,
            "max_years": self.MaxYears,
        }


# -------------------------------------------------------
# Roles
# -------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"

    RoleID = Column("roleid", Integer, primary_key=True)
    Name = Column("rolename", String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


# -------------------------------------------------------
# Users
# -------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    UserID = Column("userid", Integer, primary_key=True, autoincrement=True)
    Name = Column("name", String(100))
    Email = Column("email", String(255), unique=True, nullable=True)
    RoleID = Column("roleid", Integer, ForeignKey("roles.roleid"), default=1)
    CareerLevelID = Column("careerlevelid", Integer, ForeignKey("careerlevels.careerlevelid"))
    RangeID = Column("rangeid", Integer, ForeignKey("experienceranges.rangeid"), nullable=True)
    # ExperienceRangeID = Column("experiencerangeid", Integer, ForeignKey("experienceranges.rangeid"), nullable=True)
    CreatedAt = Column("createdat", DateTime(timezone=True), server_default=func.now())
    UpdatedAt = Column("updatedat", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    career_level = relationship("CareerLevel", back_populates="users")
    experience_range = relationship("ExperienceRange", back_populates="users", foreign_keys=[RangeID])
    social_logins = relationship("SocialLogin", back_populates="user")
    desired_jobs = relationship("DesiredJob", secondary="userdesiredjobs", back_populates="users")
    skills = relationship("Skill", secondary="userskills", back_populates="users")
    notifications = relationship("UserNotificationSetting", back_populates="user")
    scraps = relationship("UserScrap", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")


# -------------------------------------------------------
# SocialLogins
# -------------------------------------------------------
class SocialLogin(Base):
    __tablename__ = "sociallogins"

    SocialLoginID = Column("socialloginid", Integer, primary_key=True, autoincrement=True)
    UserID = Column("userid", Integer, ForeignKey("users.userid"), nullable=False)
    Provider = Column("provider", String(20), nullable=False)
    ProviderUserID = Column("provideruserid", String(255), nullable=False)
    LinkedAt = Column("linkedat", DateTime(timezone=True), server_default=func.now())
    UnlinkedAt = Column("unlinkedat", DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(UserID, Provider, name="uq_sociallogins_user_provider"),
        CheckConstraint("Provider IN ('Kakao', 'Naver', 'Google')",
                        name="chk_sociallogins_provider"),
    )

    user = relationship("User", back_populates="social_logins")


# -------------------------------------------------------
# DesiredJobs + UserDesiredJobs
# -------------------------------------------------------
class DesiredJob(Base):
    __tablename__ = "desiredjobs"

    DesiredJobID = Column("desiredjobid", Integer, primary_key=True, autoincrement=True)
    JobName = Column("jobname", String(100), unique=True, nullable=False)

    users = relationship("User", secondary="userdesiredjobs", back_populates="desired_jobs")


class UserDesiredJob(Base):
    __tablename__ = "userdesiredjobs"

    UserID = Column("userid", Integer, ForeignKey("users.userid"), primary_key=True)
    DesiredJobID = Column("desiredjobid", Integer, ForeignKey("desiredjobs.desiredjobid"), primary_key=True)


# -------------------------------------------------------
# Skills + UserSkills (M2M)
# -------------------------------------------------------
class Skill(Base):
    __tablename__ = "skills"

    SkillID = Column("skillid", Integer, primary_key=True, autoincrement=True)
    SkillName = Column("skillname", String(100), unique=True, nullable=False)

    users = relationship("User", secondary="userskills", back_populates="skills")
    job_posts = relationship("JobPost", secondary="jobpostskills", back_populates="skills")


class UserSkill(Base):
    __tablename__ = "userskills"

    UserID = Column("userid", Integer, ForeignKey("users.userid"), primary_key=True)
    SkillID = Column("skillid", Integer, ForeignKey("skills.skillid"), primary_key=True)


# -------------------------------------------------------
# User Notification Settings
# -------------------------------------------------------
class UserNotificationSetting(Base):
    __tablename__ = "usernotificationsettings"

    UserNotificationID = Column("usernotificationid", Integer, primary_key=True, autoincrement=True)
    UserID = Column("userid", Integer, ForeignKey("users.userid"), nullable=False)
    NotificationType = Column("notificationtype", String(100))
    IsEnabled = Column("isenabled", Boolean, default=True)
    NotificationTime = Column("notificationtime", String(50))

    user = relationship("User", back_populates="notifications")


# -------------------------------------------------------
# Platforms
# -------------------------------------------------------
class Platform(Base):
    __tablename__ = "platforms"

    PlatformID = Column("platformid", Integer, primary_key=True, autoincrement=True)
    PlatformName = Column("platformname", String(100), unique=True, nullable=False)

    job_posts = relationship("JobPost", back_populates="platform")


# -------------------------------------------------------
# JobCategories
# -------------------------------------------------------
class JobCategory(Base):
    __tablename__ = "jobcategories"

    CategoryID = Column("categoryid", Integer, primary_key=True, autoincrement=True)
    CategoryName = Column("categoryname", String(100), nullable=False)
    ParentCategoryID = Column("parentcategoryid", Integer, ForeignKey("jobcategories.categoryid"))
    Depth = Column("depth", Integer, nullable=False, default=1)

    parent = relationship("JobCategory", remote_side=[CategoryID])
    job_posts = relationship("JobPost", back_populates="job_category")
    bootcamp_posts = relationship("BootcampPost", back_populates="job_category")


# -------------------------------------------------------
# JobPosts
# -------------------------------------------------------
class JobPost(Base):
    __tablename__ = "jobposts"

    PostID = Column("postid", Integer, primary_key=True, autoincrement=True)
    PlatformID = Column("platformid", Integer, ForeignKey("platforms.platformid"), nullable=False)
    Title = Column("title", String(255))
    CompanyName = Column("companyname", String(255))
    JobCategoryID = Column("jobcategoryid", Integer, ForeignKey("jobcategories.categoryid"), nullable=False)
    EmploymentType = Column("employmenttype", String(50))
    ExperienceRequirement = Column("experiencerequirement", String(10), nullable=False)
    MinExperienceYears = Column("minexperienceyears", Integer, default=0)
    EducationRequirement = Column("educationrequirement", String(50))
    Location = Column("location", String(255))
    MainTasks = Column("maintasks", Text)
    Qualifications = Column("qualifications", Text)
    Preferences = Column("preferences", Text)
    Benefits = Column("benefits", Text)
    Process = Column("process", Text)
    Salary = Column("salary", String(100))
    PostedDate = Column("posteddate", Date)
    CloseDate = Column("closedate", Date)
    ViewCount = Column("viewcount", Integer, default=0)
    Url = Column("url", String(500))
    Embeded = Column('embeded', Vector(768), nullable = True)
    IsActive = Column("isactive", Boolean, default=True)
    CreatedAt = Column("createdat", DateTime(timezone=True), server_default=func.now())
    UpdatedAt = Column("updatedat", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("ExperienceRequirement IN ('신입','경력')",
                        name="chk_jobposts_experience_requirement"),
    )

    platform = relationship("Platform", back_populates="job_posts")
    job_category = relationship("JobCategory", back_populates="job_posts")
    skills = relationship("Skill", secondary="jobpostskills", back_populates="job_posts")
    scraps = relationship("UserScrap", back_populates="job_post")


class JobPostSkill(Base):
    __tablename__ = "jobpostskills"

    PostID = Column("postid", Integer, ForeignKey("jobposts.postid"), primary_key=True)
    SkillID = Column("skillid", Integer, ForeignKey("skills.skillid"), primary_key=True)



# -------------------------------------------------------
# BootcampPosts
# -------------------------------------------------------
class BootcampPost(Base):
    __tablename__ = "bootcampposts"

    BootcampID = Column("bootcampid", Integer, primary_key=True, autoincrement=True)
    Title = Column("title", String(255), nullable=False)
    InstituteName = Column("institutename", String(255), nullable=False)
    JobCategoryID = Column("jobcategoryid", Integer, ForeignKey("jobcategories.categoryid"), nullable=False)
    Location = Column("location", String(255))
    OnlineOffline = Column("onlineoffline", String(10), default="온라인")
    CostSupportType = Column("costsupporttype", String(10), default="본인부담")
    EducationContent = Column("educationcontent", Text)
    Qualification = Column("qualification", Text)
    Benefits = Column("benefits", Text)
    StartDate = Column("startdate", Date)
    RegistrationDate = Column("registrationdate", Date)
    CloseDate = Column("closedate", Date)
    DetailUrl = Column("detailurl", String(500))
    Embeded = Column('embeded', Vector(768), nullable = True)
    ViewCount = Column("viewcount", Integer, default=0)
    CreatedAt = Column("createdat", DateTime(timezone=True), server_default=func.now())
    UpdatedAt = Column("updatedat", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("OnlineOffline IN ('온라인','오프라인','혼합형')"),
        CheckConstraint("CostSupportType IN ('국비지원','본인부담')"),
    )

    job_category = relationship("JobCategory", back_populates="bootcamp_posts")
    scraps = relationship("UserScrap", back_populates="bootcamp_post")


# -------------------------------------------------------
# UserScraps
# -------------------------------------------------------
class UserScrap(Base):
    __tablename__ = "userscraps"

    ScrapID = Column("scrapid", Integer, primary_key=True, autoincrement=True)
    UserID = Column("userid", Integer, ForeignKey("users.userid"), nullable=False)
    PostType = Column("posttype", String(20), nullable=False)
    JobPostID = Column("jobpostid", Integer, ForeignKey("jobposts.postid"))
    BootcampPostID = Column("bootcamppostid", Integer, ForeignKey("bootcampposts.bootcampid"))
    ScrappedAt = Column("scrappedat", DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(PostType = 'Job' AND JobPostID IS NOT NULL AND BootcampPostID IS NULL) "
            "OR (PostType = 'Bootcamp' AND BootcampPostID IS NOT NULL AND JobPostID IS NULL)",
            name="chk_userscraps_only_one_ref"
        ),
        CheckConstraint("PostType IN ('Job','Bootcamp')"),
          Index("uq_userscraps_job", UserID, JobPostID, unique=True,
              postgresql_where=(PostType == 'Job')),
          Index("uq_userscraps_bootcamp", UserID, BootcampPostID, unique=True,
              postgresql_where=(PostType == 'Bootcamp')),
    )

    user = relationship("User", back_populates="scraps")
    job_post = relationship("JobPost", back_populates="scraps")
    bootcamp_post = relationship("BootcampPost", back_populates="scraps")


# -------------------------------------------------------
# UserSessions
# -------------------------------------------------------
class UserSession(Base):
    __tablename__ = "usersessions"

    SessionID = Column("sessionid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserID = Column("userid", Integer, ForeignKey("users.userid"), nullable=False)
    AccessToken = Column("accesstoken", String(1000), nullable=False)
    RefreshToken = Column("refreshtoken", String(1000))
    ExpiresAt = Column("expiresat", DateTime(timezone=True), nullable=False)
    CreatedAt = Column("createdat", DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")