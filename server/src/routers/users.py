from fastapi import APIRouter, \
                    Depends, \
                    Response, \
                    Request, \
                    status, \
                    HTTPException, \
                    Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any, cast, Union
from src.database import get_db
from src import models
from datetime import datetime
from fastapi import Depends as _Depends
import logging

logger = logging.getLogger(__name__)
from src.schemas import UserScrapPost


router = APIRouter(prefix="/users", tags=['유저 프로필 기능'])

# schemas 부분
class ProfileOut(BaseModel):
    user_id: int
    name: Optional[str]
    email: str
    experience_range: Optional[str] = None
    career_level: Optional[str] = None
    skills: List[str] = []
    desired_jobs: List[str] = []
    recentViews: Optional[List[str]] = None

    class Config:
        orm_mode = True


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    career_level: Optional[Union[str, int]] = None
    experience_range: Optional[Union[str, int]] = None
    skills: Optional[List[str]] = None
    desired_jobs: Optional[List[str]] = None
    recentViews: Optional[List[str]] = None

class JobPostOut(BaseModel):
    id: int
    title: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        orm_mode = True

class BootcampPostOut(BaseModel):
    id: int
    title: Optional[str] = None
    institute_name: Optional[str] = None

    class Config:
        orm_mode = True

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
    post_type: Optional[str] = None
    job_post_id: Optional[int] = None
    bootcamp_post_id: Optional[int] = None
    job_post: Optional[JobPostOut] = None
    bootcamp_post: Optional[BootcampPostOut] = None

    class Config:
        orm_mode = True

class UserNotifications(BaseModel):
    notification_type: Optional[str] = None
    isenabled: Optional[bool] = None
    notificationtime: Optional[str] = None

    class Config:
        orm_mode = True

class UserNotificationsUpdate(BaseModel):
    notification_type: Optional[str] = None
    isenabled: Optional[bool] = None
    notificationtime: Optional[str] = None

    class Config:
        orm_mode = True
    
def get_user_data(db: Session, user_id: int):
    # 관련 관계를 명시적으로 eager load 하여
    # 저장된 스킬/희망직무/커리어 레벨을 확실히 조회하도록 합니다.
    user = (
        db.query(models.User)
        .options(
            joinedload(models.User.career_level),
            joinedload(models.User.skills),
            joinedload(models.User.desired_jobs),
        )
        .filter(models.User.UserID == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

def get_user_scrap(db: Session, user_id: int):
    return (
        db.query(models.UserScrap)
        .options(joinedload(models.UserScrap.job_post))
        .options(joinedload(models.UserScrap.bootcamp_post))
        .filter(models.UserScrap.UserID == user_id)
        .all()
    )

def get_user_notifications(db: Session, user_id: int):
    notifications = (
        db.query(models.UserNotificationSetting)
        .filter(models.UserNotificationSetting.UserID == user_id)
        .all()
    )

    if not notifications:
        raise HTTPException(status_code=404, detail="알림 항목을 찾을 수 없습니다.")
    return notifications


def get_current_user(db: Session = _Depends(get_db), user_id: Optional[str] = Cookie(None), session_id: Optional[str] = Cookie(None)):
    """Dependency: 쿠키 기반 세션을 검사하고 현재 User 객체를 반환합니다.

    - 소셜 로그인에서 발급한 `user_id`/`session_id` 쿠키를 사용합니다.
    - 세션이 없거나 만료되었으면 HTTPException(401)을 발생시킵니다.
    """
    if not user_id or not session_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        session = (
            db.query(models.UserSession)
            .filter(
                models.UserSession.SessionID == session_id,
                models.UserSession.UserID == int(user_id),
            )
            .first()
        )

        if not session:
            raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다.")

        if session.ExpiresAt < datetime.now():
            db.delete(session)
            db.commit()
            raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")

        user = db.query(models.User).filter(models.User.UserID == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="존재하지 않는 사용자입니다.")

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 검증 중 오류: {e}")

@router.get("/{user_id}", response_model=ProfileOut)
def read_profile(user_id: int, db: Session = Depends(get_db)):
    user = get_user_data(db, user_id)
    career_name = None
    experience_name = None
    user_skills = [s.SkillName for s in user.skills]
    user_desired_jobs = [j.JobName for j in user.desired_jobs]

    career_name = user.career_level.CareerName if user.career_level else None
    experience_name = user.experience_range.RangeName if getattr(user, 'experience_range', None) else None

    return ProfileOut(
        user_id=user.UserID,
        name=user.Name,
        email=user.Email,
        career_level=career_name,
        experience_range=experience_name,
        skills=user_skills,
        desired_jobs=user_desired_jobs,
        recentViews=None
    )



@router.put("/{user_id}", response_model=ProfileOut)
def update_profile(user_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    logger.info(f"프로필 업데이트 시작 - user_id: {user_id}, data: {data}")
    user = get_user_data(db, user_id)

    # 이름
    if data.name is not None:
        user.Name = data.name
    
    # 이메일
    if data.email is not None:
        user.Email = data.email

    # 경력 레벨
    if data.career_level is not None:
        # 문자열인 경우
        if isinstance(data.career_level, str):
            career = db.query(models.CareerLevel).filter(
                models.CareerLevel.CareerName == data.career_level
            ).first()
            if not career:
                raise HTTPException(400, "존재하지 않는 커리어 레벨 이름입니다.")

            user.CareerLevelID = career.CareerLevelID

        # 숫자인 경우
        elif isinstance(data.career_level, int):
            career = db.query(models.CareerLevel).filter(
                models.CareerLevel.CareerLevelID == data.career_level
            ).first()
            if not career:
                raise HTTPException(400, "유효하지 않은 커리어 레벨 ID입니다.")

            user.CareerLevelID = data.career_level

    # 경력 구간 (experience range)
    if data.experience_range is not None:
        # 문자열인 경우: 이름으로 찾기
        if isinstance(data.experience_range, str):
            if data.experience_range:  # 빈 문자열이 아닌 경우
                exp = db.query(models.ExperienceRange).filter(
                    models.ExperienceRange.RangeName == data.experience_range
                ).first()
                if exp:
                    user.ExperienceRangeID = exp.RangeID
                else:
                    user.ExperienceRangeID = None
            else:
                user.ExperienceRangeID = None

        # 숫자인 경우: ID로 설정
        elif isinstance(data.experience_range, int):
            if data.experience_range and data.experience_range > 0:  # 유효한 ID인 경우
                exp = db.query(models.ExperienceRange).filter(
                    models.ExperienceRange.RangeID == data.experience_range
                ).first()
                if exp:
                    user.ExperienceRangeID = data.experience_range
                    logger.info(f"경력 구간 저장: user_id={user_id}, range_id={data.experience_range}")
                else:
                    user.ExperienceRangeID = None
            else:
                # 0이나 음수는 null로 처리
                user.ExperienceRangeID = None

            

    # 스킬
    if data.skills is not None:
        new_skill_objs = []
        for name in data.skills:
            skill = db.query(models.Skill).filter(models.Skill.SkillName == name).first()
            if not skill:
                skill = models.Skill(SkillName=name)
                db.add(skill)
                # flush to assign PK without committing the whole transaction yet
                db.flush()
            new_skill_objs.append(skill)

        # replace user's skills with the resolved Skill objects
        user.skills = new_skill_objs


    # 4) 희망직무
    if data.desired_jobs is not None:
        new_job_objs = []
        for name in data.desired_jobs:
            job = db.query(models.DesiredJob).filter(models.DesiredJob.JobName == name).first()
            if not job:
                job = models.DesiredJob(JobName=name)
                db.add(job)
                db.flush()
            new_job_objs.append(job)

        # replace user's desired jobs with the resolved DesiredJob objects
        user.desired_jobs = new_job_objs

    db.commit()
    db.refresh(user)
    
    logger.info(f"프로필 업데이트 완료 - user_id: {user_id}")

    return read_profile(user.UserID, db)


@router.get("/me", response_model=ProfileOut)
def get_my_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인한 사용자의 프로필 조회"""
    return read_profile(current_user.UserID, db)


@router.patch("/me", response_model=ProfileOut)
def update_my_profile(data: ProfileUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인한 사용자의 프로필 업데이트

    `get_current_user` 종속성으로 현재 로그인한 User 객체를 주입받아
    동일한 `update_profile` 로직을 재사용합니다.
    """
    return update_profile(current_user.UserID, data, db)


# @router.get("/{user_id}/scraps", response_model=List[UserScrapGet])
# def read_userscrap(user_id: int, db: Session = Depends(get_db)):
#     scraps = get_user_scrap(db, user_id)

#     result = []

#     for scrap in scraps:

#         if scrap.PostType == "Job" and scrap.job_post:
#             job_post = JobPostOut(
#                 id=scrap.job_post.PostID,
#                 title=scrap.job_post.Title,
#                 company_name=scrap.job_post.CompanyName,
#             )
#         else:
#             job_post = None

#         if scrap.PostType == "Bootcamp" and scrap.bootcamp_post:
#             bootcamp_post = BootcampPostOut(
#                 id=scrap.bootcamp_post.BootcampID,
#                 title=scrap.bootcamp_post.Title,
#                 institute_name=scrap.bootcamp_post.InstituteName,
#             )
#         else:
#             bootcamp_post = None

#         result.append(
#             UserScrapGet(
#                 post_type=scrap.PostType,
#                 job_post_id=scrap.JobPostID,
#                 bootcamp_post_id=scrap.BootcampPostID,
#                 job_post=job_post,
#                 bootcamp_post=bootcamp_post
#             )
#         )
#     return result


# @router.post("/me/scraps", response_model=Dict[str, Any])
# def create_my_scrap(data: UserScrapPost, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """현재 로그인한 사용자의 스크랩 추가 (Job 또는 Bootcamp)."""
#     try:
#         if data.post_type.value.lower() == 'job':
#             # 이미 존재하는지 확인
#             existing = db.query(models.UserScrap).filter(
#                 models.UserScrap.UserID == current_user.UserID,
#                 models.UserScrap.PostType == 'Job',
#                 models.UserScrap.JobPostID == data.target_id,
#             ).first()
#             if existing:
#                 return {"status": "ok", "message": "already_scrapped"}

#             scrap = models.UserScrap(
#                 UserID=current_user.UserID,
#                 PostType='Job',
#                 JobPostID=data.target_id,
#             )
#         else:
#             existing = db.query(models.UserScrap).filter(
#                 models.UserScrap.UserID == current_user.UserID,
#                 models.UserScrap.PostType == 'Bootcamp',
#                 models.UserScrap.BootcampPostID == data.target_id,
#             ).first()
#             if existing:
#                 return {"status": "ok", "message": "already_scrapped"}

#             scrap = models.UserScrap(
#                 UserID=current_user.UserID,
#                 PostType='Bootcamp',
#                 BootcampPostID=data.target_id,
#             )

#         db.add(scrap)
#         db.commit()
#         db.refresh(scrap)
#         return {"status": "ok", "scrap_id": scrap.ScrapID}
#     except Exception as e:
#         db.rollback()
#         logger.exception("스크랩 생성 실패")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/me/scraps", response_model=Dict[str, Any])
# def delete_my_scrap(data: UserScrapPost, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """현재 로그인한 사용자의 스크랩 삭제"""
#     try:
#         if data.post_type.value.lower() == 'job':
#             scrap = db.query(models.UserScrap).filter(
#                 models.UserScrap.UserID == current_user.UserID,
#                 models.UserScrap.PostType == 'Job',
#                 models.UserScrap.JobPostID == data.target_id,
#             ).first()
#         else:
#             scrap = db.query(models.UserScrap).filter(
#                 models.UserScrap.UserID == current_user.UserID,
#                 models.UserScrap.PostType == 'Bootcamp',
#                 models.UserScrap.BootcampPostID == data.target_id,
#             ).first()

#         if not scrap:
#             return {"status": "ok", "message": "not_found"}

#         db.delete(scrap)
#         db.commit()
#         return {"status": "ok", "message": "deleted"}
#     except Exception as e:
#         db.rollback()
#         logger.exception("스크랩 삭제 실패")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/notifications", response_model=List[UserNotifications])
def read_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = get_user_notifications(db, user_id)

    if not notifications:
        raise HTTPException(404, "알림 항목을 찾을 수 없습니다.")
    
    return [
        UserNotifications(
            notification_type=n.NotificationType,
            isenabled=n.IsEnabled,
            notificationtime=n.NotificationTime,
        )
        for n in notifications
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)