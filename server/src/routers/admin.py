from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Cookie, Path)
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from src.database import get_db
from src import models
from datetime import datetime
from src.schemas import (
    UserOut, UserRoleUpdate, JobPostOut,
    JobPostUpdate, BootcampOut, BootcampUpdate
)

router = APIRouter(prefix = "/admin", tags = ["admin"])

# ========== 권한 확인 함수 ==========

def check_admin_role(
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Cookie(None, alias="user_id"),      # 로그인한 사람의 ID
    current_session_id: Optional[str] = Cookie(None, alias="session_id")    # 로그인한 사람의 sesseion
) -> models.User:
    """
    관리자 역할 확인
    현재 사용자가 관리자인지 확인하는 의존성
        - 로그인한 사용자(일반 사용자 or 관리자)를 확인하기 위한 함수
          => Cookie에서 정보를 가져와야 함.
    """
    # 1. 세션 검증
    if not current_user_id or not current_session_id:
        raise HTTPException(status_code = 401, detail = "로그인이 필요합니다.")

    try:
        session = (
            db.query(models.UserSession)
            .filter(
                models.UserSession.SessionID == current_session_id,
                models.UserSession.UserID == int(current_user_id),
            )
            .first()
        )

        if not session:
            raise HTTPException(status_code = 401, detail = "유효하지 않은 세션입니다.")

        if session.ExpiresAt < datetime.now():
            db.delete(session)
            db.commit()
            raise HTTPException(status_code = 401, detail = "세션이 만료되었습니다.")

        # 2. 사용자 조회
        user = db.query(models.User).filter(models.User.UserID == int(current_user_id)).first()
        if not user:
            raise HTTPException(status_code = 401, detail = "존재하지 않는 사용자입니다.")

        # 3. 관리자 권한 확인 (RoleID가 2인 경우 관리자)
        if not user.RoleID or user.RoleID != 2:
            raise HTTPException(status_code = 403, detail = "관리자 권한이 필요합니다.")

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"권한 검증 중 오류: {e}")


# ========== 회원 관리 API ==========

@router.get("/users", response_model = List[UserOut])
def get_all_users(db: Session = Depends(get_db),
                  admin_user: models.User = Depends(check_admin_role)):
    """
    모든 사용자 조회 (관리자 먼저, 그 다음 일반사용자 순으로 정렬)
    """
    try:
        users = db.query(models.User).order_by(models.User.RoleID.desc(), models.User.UserID.asc()).all()
        # 반환 형태를 프론트엔드가 기대하는 형태로 매핑
        result = []
        for u in users:
            # RoleID를 직접 사용 (기본값 1)
            role_id = u.RoleID if u.RoleID else 1
            result.append({
                "userid": u.UserID,
                "email": u.Email,
                "name": u.Name,
                "role": role_id,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to get users: {str(e)}")


@router.delete("/users/{user_id}")
def delete_user(user_id: int = Path(..., description = "삭제할 유져 ID"),
                db: Session = Depends(get_db),
                admin_user: models.User = Depends(check_admin_role)):
    """
    사용자 삭제
    """
    try:
        user = db.query(models.User).filter(models.User.UserID == user_id).first()
        if not user:
            raise HTTPException(status_code = 404, detail = "User not found")

        # 사용자와 관련된 데이터 정리
        db.query(models.UserDesiredJob).filter(
            models.UserDesiredJob.UserID == user_id
        ).delete()
        db.query(models.UserSkill).filter(
            models.UserSkill.UserID == user_id
        ).delete()
        db.query(models.UserNotificationSetting).filter(
            models.UserNotificationSetting.UserID == user_id
        ).delete()
        db.query(models.UserScrap).filter(
            models.UserScrap.UserID == user_id
        ).delete()
        db.query(models.SocialLogin).filter(
            models.SocialLogin.UserID == user_id
        ).delete()

        # 사용자 삭제
        db.delete(user)
        db.commit()

        return {
            "message": "User deleted successfully",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to delete user: {str(e)}")


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(user_id: int,
                     data: UserRoleUpdate,
                     db: Session = Depends(get_db),
                     admin_user: models.User = Depends(check_admin_role)):
    """
    사용자 역할 변경 (roleid: 1 for user, 2 for admin)
    """
    try:
        # 역할 ID 검증
        if data.roleid not in [1, 2]:
            raise HTTPException(status_code = 400, detail = "Invalid roleid. Must be 1 (user) or 2 (admin)")

        user = db.query(models.User).filter(models.User.UserID == user_id).first()
        if not user:
            raise HTTPException(status_code = 404, detail = "User not found")

        user.RoleID = data.roleid
        db.commit()
        db.refresh(user)

        # 반환 형태를 프론트엔드가 기대하는 형태로 매핑
        return {
            "userid": user.UserID,
            "email": user.Email,
            "name": user.Name,
            "role": user.RoleID,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to update user role: {str(e)}")


# ========== 채용 공고 관리 API ==========

@router.get("/jobposts", response_model = List[JobPostOut])
def get_all_jobposts(db: Session = Depends(get_db),
                     admin_user: models.User = Depends(check_admin_role)):
    """
    모든 채용 공고 조회
    """
    try:
        # JobPost 모델은 내부적으로 PostID, Title 등을 사용하므로
        # 프론트가 기대하는 필드명(jobid, jobtitle, jobdescription)으로 매핑
        jobposts = db.query(models.JobPost).all()
        result = []
        for j in jobposts:
            result.append({
                "jobid": getattr(j, 'PostID', None),
                "jobtitle": getattr(j, 'Title', '') or '',
                "company": getattr(j, 'CompanyName', None) or '',
                "jobdescription": getattr(j, 'MainTasks', None) or getattr(j, 'Qualifications', None) or '',
            })
        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to get job posts: {str(e)}")


@router.patch("/jobposts/{job_id}", response_model = JobPostOut)
def update_jobpost(job_id: int,
                   data: JobPostUpdate,
                   db: Session = Depends(get_db),
                   admin_user: models.User = Depends(check_admin_role)):
    """
    채용 공고 수정
    """
    try:
        jobpost = db.query(models.JobPost).filter(models.JobPost.PostID == job_id).first()
        if not jobpost:
            raise HTTPException(status_code = 404, detail = "Job post not found")

        if data.jobtitle is not None:
            jobpost.Title = data.jobtitle
        if data.jobdescription is not None:
            jobpost.MainTasks = data.jobdescription

        jobpost.UpdatedAt = datetime.now()
        db.commit()
        db.refresh(jobpost)

        # 반환 형태를 프론트엔드가 기대하는 형태로 매핑
        return {
            "jobid": jobpost.PostID,
            "jobtitle": jobpost.Title or '',
            "jobdescription": jobpost.MainTasks or jobpost.Qualifications or '',
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to update job post: {str(e)}")


@router.delete("/jobposts/{job_id}")
def delete_jobpost(job_id: int,
                   db: Session = Depends(get_db),
                   admin_user: models.User = Depends(check_admin_role)):
    """
    채용 공고 삭제
    """
    try:
        jobpost = db.query(models.JobPost).filter(models.JobPost.PostID == job_id).first()
        if not jobpost:
            raise HTTPException(status_code = 404, detail = "Job post not found")

        # 관련 데이터 정리
        db.query(models.JobPostSkill).filter(
            models.JobPostSkill.PostID == job_id
        ).delete()
        db.query(models.UserScrap).filter(
            models.UserScrap.JobPostID == job_id
        ).delete()

        db.delete(jobpost)
        db.commit()

        return {"message": "Job post deleted successfully", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to delete job post: {str(e)}")


# ========== 부트캠프 관리 API ==========

@router.get("/bootcamps", response_model = List[BootcampOut])
def get_all_bootcamps(db: Session = Depends(get_db),
                      admin_user: models.User = Depends(check_admin_role)):
    """
    모든 부트캠프 조회
    """
    try:
        # BootcampPost 모델 사용 (테이블명: bootcampposts)
        bootcamps = db.query(models.BootcampPost).all()
        result = []
        for b in bootcamps:
            result.append({
                "bootcampid": getattr(b, 'BootcampID', None),
                "bootcampname": getattr(b, 'Title', '') or '',
                "institution": getattr(b, 'InstituteName', '') or '',
                "description": getattr(b, 'EducationContent', None) or getattr(b, 'Benefits', None) or '',
            })
        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Failed to get bootcamps: {str(e)}")


@router.patch("/bootcamps/{bootcamp_id}", response_model = BootcampOut)
def update_bootcamp(bootcamp_id: int,
                    data: BootcampUpdate,
                    db: Session = Depends(get_db),
                    admin_user: models.User = Depends(check_admin_role)):
    """
    부트캠프 수정
    """
    try:
        bootcamp = db.query(models.BootcampPost).filter(
            models.BootcampPost.BootcampID == bootcamp_id
        ).first()
        if not bootcamp:
            raise HTTPException(status_code = 404, detail = "Bootcamp not found")

        if data.bootcampname is not None:
            bootcamp.Title = data.bootcampname
        if data.institution is not None:
            bootcamp.InstituteName = data.institution
        if data.description is not None:
            bootcamp.EducationContent = data.description

        bootcamp.UpdatedAt = datetime.now()
        db.commit()
        db.refresh(bootcamp)

        # 반환 형태를 프론트엔드가 기대하는 형태로 매핑
        return {
            "bootcampid": bootcamp.BootcampID,
            "bootcampname": bootcamp.Title or '',
            "institution": bootcamp.InstituteName or '',
            "description": bootcamp.EducationContent or bootcamp.Benefits or '',
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to update bootcamp: {str(e)}")


@router.delete("/bootcamps/{bootcamp_id}")
def delete_bootcamp(bootcamp_id: int,
                    db: Session = Depends(get_db),
                    admin_user: models.User = Depends(check_admin_role)):
    """
    부트캠프 삭제
    """
    try:
        bootcamp = db.query(models.BootcampPost).filter(
            models.BootcampPost.BootcampID == bootcamp_id
        ).first()
        if not bootcamp:
            raise HTTPException(status_code = 404, detail = "Bootcamp not found")

        # 관련 데이터 정리 (필요시)
        db.query(models.UserScrap).filter(
            models.UserScrap.BootcampPostID == bootcamp_id
        ).delete()

        db.delete(bootcamp)
        db.commit()

        return {"message": "Bootcamp deleted successfully", "bootcamp_id": bootcamp_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Failed to delete bootcamp: {str(e)}")
# Note: 실제로는 JWT 인증을 통해 현재 사용자의 역할을 확인하는 로직이 필요합니다.