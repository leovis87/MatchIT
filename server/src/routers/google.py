import os
import httpx
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Cookie, Response, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from datetime import datetime, timedelta
from src.models import User, SocialLogin, UserSession
from typing import Optional

ENV_PATH = Path(__file__).parent.parent.parent / '.env'
load_dotenv(ENV_PATH)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/auth/google", tags=["구글 소셜로그인 기능"])


# ------------------------------------------------------------
# 1) 구글 로그인 Redirect
# ------------------------------------------------------------
@router.get("/login")
async def google_login():
    """구글 로그인 페이지로 이동"""
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&prompt=consent"
    )
    return RedirectResponse(url=google_auth_url)


# ------------------------------------------------------------
# 2) 구글 OAuth Callback 처리
# ------------------------------------------------------------
@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):

    # 1. 토큰 교환
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    expires_in = token_json.get("expires_in", 3600 * 6)

    if not access_token:
        return JSONResponse(
            status_code=400,
            content={"error": "토큰 발급 실패", "details": token_json},
        )

    # 2. 사용자 정보 가져오기
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)

    user_json = user_response.json()

    google_id = user_json.get("id")
    google_email = user_json.get("email")
    google_name = user_json.get("name", "Unknown")
    google_picture = user_json.get("picture")

    newly_created = False

    # ------------------------------------------------------------
    # 3) DB 저장 로직
    # ------------------------------------------------------------
    try:
        oauth_account = (
            db.query(SocialLogin)
            .filter(
                SocialLogin.Provider == "Google",
                SocialLogin.ProviderUserID == str(google_id),
            )
            .first()
        )

        user = None

        if oauth_account:
            # 기존 사용자
            # 기존 세션 제거
            old_sessions = db.query(UserSession).filter(
                UserSession.UserID == oauth_account.UserID
            )
            for s in old_sessions:
                db.delete(s)

            oauth_account.UnlinkedAt = None
            user = oauth_account.user

        else:
            # 신규 사용자
            if google_email:
                user = db.query(User).filter(User.Email == google_email).first()

            if not user:
                user = User(
                    Email = google_email if google_email else f"google_{google_id}@no-email.com",
                    Name = google_name,
                )
                db.add(user)
                db.flush()
                newly_created = True

            new_oauth = SocialLogin(
                UserID = user.UserID,
                Provider = "Google",
                ProviderUserID = str(google_id),
                LinkedAt = datetime.now(),
                UnlinkedAt = None,
            )
            db.add(new_oauth)

        db.commit()
        db.refresh(user)

    except Exception as e:
        db.rollback()
        return JSONResponse({"error": "DB 처리 실패", "details": str(e)}, status_code=500)

    # ------------------------------------------------------------
    # 4) 세션 저장
    # ------------------------------------------------------------
    try:
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        session = UserSession(
            SessionID = session_id,
            UserID = user.UserID,
            AccessToken = access_token,
            RefreshToken = refresh_token,
            ExpiresAt = expires_at,
        )
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        return JSONResponse({"error": "세션 저장 실패", "details": str(e)}, status_code=500)

    # ------------------------------------------------------------
    # 5) 쿠키 + 프론트 리다이렉트
    # ------------------------------------------------------------
    if newly_created:
        html = f"""
        <html><head>
        <script>
            localStorage.setItem('isLogin', 'true');
            localStorage.setItem('isNewUser', 'true');
            window.location.href = '{FRONTEND_URL}/callback?signup=true';
        </script>
        </head></html>
        """
    else:
        html = f"""
        <html><head>
        <script>
            localStorage.setItem('isLogin', 'true');
            window.location.href = '{FRONTEND_URL}/callback';
        </script>
        </head></html>
        """

    response = HTMLResponse(html)

    cookie_opt = dict(
        httponly = True,
        secure = False,
        samesite = "lax",
        path = "/",
    )

    response.set_cookie("session_id", str(session_id), max_age=60 * 60 * 24 * 30, **cookie_opt)
    response.set_cookie("user_id", str(user.UserID), max_age=60 * 60 * 24 * 30, **cookie_opt)

    # UI용
    response.set_cookie(
        "is_login",
        "true",
        httponly = False,
        secure = False,
        samesite = "lax",
        path = "/",
    )

    return response


# ------------------------------------------------------------
# 6) 로그인 상태 확인 API (카카오와 동일)
# ------------------------------------------------------------
@router.get("/me")
async def get_current_user(
    user_id: Optional[str] = Cookie(None),
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    if not user_id or not session_id:
        return {"isLoggedIn": False, "user": None}

    try:
        user_id_int = int(user_id)
    except:
        return {"isLoggedIn": False, "user": None}

    session = (
        db.query(UserSession)
        .filter(UserSession.SessionID == session_id, UserSession.UserID == user_id_int)
        .first()
    )

    if not session or session.ExpiresAt < datetime.now():
        return {"isLoggedIn": False, "user": None}

    user = db.query(User).filter(User.UserID == user_id_int).first()
    if not user:
        return {"isLoggedIn": False, "user": None}

    # role 정보 로드
    db.refresh(user, ["role"])

    return {
        "isLoggedIn": True,
        "user": {
            "id": user.UserID,
            "name": user.Name,
            "email": user.Email,
            "role": user.role.Name if user.role else "user",
        },
    }


# ------------------------------------------------------------
# 7) 로그아웃 (카카오와 완전히 동일)
# ------------------------------------------------------------
@router.get("/logout")
async def google_logout(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    user_id: Optional[str] = Cookie(None),
    google_access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    print(f"[GOOGLE_LOGOUT] user_id={user_id}, session_id={session_id}")

    # Google 토큰 무효화
    if google_access_token:
        try:
            revoke_url = f"https://oauth2.googleapis.com/revoke?token={google_access_token}"
            async with httpx.AsyncClient() as client:
                await client.post(revoke_url)
            print("[GOOGLE_LOGOUT] 토큰 무효화 성공")
        except Exception as e:
            print("[GOOGLE_LOGOUT] 토큰 무효화 실패", e)

    # 쿠키 삭제
    def clear_cookies(resp):
        opts = dict(path="/", httponly=True, secure=False, samesite="lax", max_age=0)
        opts_js = dict(path="/", httponly=False, secure=False, samesite="lax", max_age=0)

        resp.delete_cookie("session_id", **opts)
        resp.delete_cookie("user_id", **opts)
        resp.delete_cookie("google_access_token", **opts)
        resp.delete_cookie("google_refresh_token", **opts)
        resp.delete_cookie("is_login", **opts_js)
        return resp

    # DB 세션 삭제
    if session_id:
        try:
            s = db.query(UserSession).filter(UserSession.SessionID == session_id).first()
            if s:
                db.delete(s)
                db.commit()
        except Exception as e:
            db.rollback()
            print("[GOOGLE_LOGOUT] DB 세션 삭제 실패:", e)

    # 소셜 unlink
    if user_id:
        try:
            accs = db.query(SocialLogin).filter(SocialLogin.UserID == int(user_id)).all()
            for acc in accs:
                acc.UnlinkedAt = datetime.now()
            db.commit()
        except Exception as e:
            db.rollback()
            print("[GOOGLE_LOGOUT] Unlink 실패:", e)

    html = """
    <html><head>
    <script>
        alert("로그아웃 되었습니다.");
        window.location.href = "/";
    </script>
    </head></html>
    """

    response = HTMLResponse(html)
    return clear_cookies(response)