import os
import httpx
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Cookie, Response, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from src.database import get_db
from src.models import User, SocialLogin, UserSession

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_PATH)

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/auth/kakao", tags=["카카오 소셜로그인 기능"])


# -------------------------
# 1) 카카오 로그인 시작
# -------------------------
@router.get("/login")
async def kakao_login():
    login_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code&client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}&prompt=login"
    )
    return RedirectResponse(url=login_url)


# -------------------------
# 2) 카카오 콜백
# -------------------------
@router.get("/callback")
async def kakao_callback(code: str, db: Session = Depends(get_db)):

    # 1. 토큰 교환
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "client_secret": KAKAO_CLIENT_SECRET,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=token_data)

    token_json = token_res.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    expires_in = token_json.get("expires_in", 60 * 60 * 6)

    if not access_token:
        return JSONResponse(
            status_code=400,
            content={"error": "토큰 발급 실패", "details": token_json},
        )

    # 2. 사용자 정보 가져오기
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        user_res = await client.get(user_info_url, headers=headers)

    user_json = user_res.json()
    kakao_id = user_json.get("id")
    kakao_account = user_json.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    kakao_nickname = (
        profile.get("nickname")
        or user_json.get("properties", {}).get("nickname")
        or "Unknown"
    )

    kakao_email = kakao_account.get("email")
    kakao_gender = kakao_account.get("gender")

    # 3. 회원가입 / 로그인 처리
    try:
        oauth_account = (
            db.query(SocialLogin)
            .filter(
                SocialLogin.Provider == "Kakao",
                SocialLogin.ProviderUserID == str(kakao_id),
            )
            .first()
        )

        newly_created = False

        if oauth_account:
            # 기존 유저
            user = oauth_account.user

            # 기존 세션 삭제
            old_sessions = (
                db.query(UserSession)
                .filter(UserSession.UserID == oauth_account.UserID)
                .all()
            )
            for s in old_sessions:
                db.delete(s)

            oauth_account.UnlinkedAt = None

        else:
            # 신규 가입
            user = None

            if kakao_email:
                user = db.query(User).filter(User.Email == kakao_email).first()

            if not user:
                user = User(
                    Email=kakao_email
                    if kakao_email
                    else f"kakao_{kakao_id}@no-email.com",
                    Name=kakao_nickname,
                )
                db.add(user)
                db.flush()
                newly_created = True

            new_oauth = SocialLogin(
                UserID=user.UserID,
                Provider="Kakao",
                ProviderUserID=str(kakao_id),
                LinkedAt=datetime.now(),
                UnlinkedAt=None,
            )
            db.add(new_oauth)

        db.commit()
        db.refresh(user)

        # role 정보 로드
        db.refresh(user, ["role"])

    except Exception as e:
        db.rollback()
        logger.exception("DB 처리 중 예외 발생")
        return JSONResponse(
            status_code=500,
            content={"error": "DB 처리 실패", "details": str(e)},
        )

    # 4. 세션 DB 저장
    try:
        session_id = str(uuid.uuid4())  # 문자열로 저장
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        session = UserSession(
            SessionID=session_id,
            UserID=user.UserID,
            AccessToken=access_token,
            RefreshToken=refresh_token,
            ExpiresAt=expires_at,
        )
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("세션 저장 중 예외 발생")
        return JSONResponse(
            status_code=500,
            content={"error": "세션 저장 실패", "details": str(e)},
        )

    # 5. 프론트 이동 HTML
    if newly_created:
        redirect_url = f"{FRONTEND_URL}/callback?signup=true"
    else:
        redirect_url = f"{FRONTEND_URL}/callback"

    html = f"""
    <html><head><script>
        try {{ localStorage.setItem('isLogin', 'true'); }} catch(e) {{}}
        window.location.href = "{redirect_url}";
    </script></head></html>
    """
    response = HTMLResponse(html)

    # HttpOnly 쿠키 설정
    cookie_opt = {
        "httponly": True,
        "secure": False,
        "samesite": "lax",
        "path": "/",
    }

    response.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 30, **cookie_opt)
    response.set_cookie("user_id", str(user.UserID), max_age=60 * 60 * 24 * 30, **cookie_opt)

    # JS 접근용 쿠키
    response.set_cookie(
        "is_login",
        "true",
        httponly = False,
        secure = False,
        samesite = "lax",
        path = "/",
    )

    return response


# -------------------------
# 3) 로그인 상태 확인
# -------------------------
@router.get("/me")
async def get_current_user(
    user_id: Optional[str] = Cookie(None),
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    logger.info(f"get_current_user called with user_id: {user_id}, session_id: {session_id}")

    if not user_id or not session_id:
        logger.info("Missing user_id or session_id")
        return {"isLoggedIn": False, "user": None}

    try:
        session = (
            db.query(UserSession)
            .filter(
                UserSession.SessionID == session_id,
                UserSession.UserID == int(user_id),
            )
            .first()
        )

        if not session:
            logger.info("Session not found in DB")
            return {"isLoggedIn": False, "user": None}

        if session.ExpiresAt < datetime.now():
            logger.info("Session expired")
            db.delete(session)
            db.commit()
            return {"isLoggedIn": False, "user": None}

        user = db.query(User).filter(User.UserID == int(user_id)).first()
        if not user:
            return {"isLoggedIn": False, "user": None}

        # role 정보 로드
        db.refresh(user, ["role"])

        logger.info(f"User authenticated: {user.Name}, role: {user.role.Name if user.role else 'user'}")

        return {
            "isLoggedIn": True,
            "user": {
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
            },
        }

    except Exception:
        logger.error(f"Error in get_current_user: {e}")
        return {"isLoggedIn": False, "user": None}


# -------------------------
# 4) 카카오 로그아웃
# -------------------------
@router.get("/logout")
async def kakao_logout(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    user_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):

    print(f"[LOGOUT] 시작 user_id={user_id}, session_id={session_id}")

    # 1. 세션 삭제
    if session_id:
        session = (
            db.query(UserSession)
            .filter(UserSession.SessionID == session_id)
            .first()
        )
        if session:
            db.delete(session)
            db.commit()
            print("[LOGOUT] 세션 삭제 완료")

    # 2. 소셜 계정 unlink (로그인 상태 초기화 목적)
    if user_id:
        oauth_list = db.query(SocialLogin).filter(SocialLogin.UserID == int(user_id)).all()
        for oauth in oauth_list:
            oauth.UnlinkedAt = datetime.now()
        db.commit()

    # 3. 쿠키 삭제
    response = HTMLResponse(
        """
        <script>
            alert("로그아웃 되었습니다.");
            window.location.href = "/";
        </script>
        """
    )

    delete_opt = {"path": "/", "httponly": True, "secure": False, "samesite": "lax"}
    delete_opt_js = {"path": "/", "httponly": False, "secure": False, "samesite": "lax"}

    response.delete_cookie("session_id", **delete_opt)
    response.delete_cookie("user_id", **delete_opt)
    response.delete_cookie("is_login", **delete_opt_js)

    return response