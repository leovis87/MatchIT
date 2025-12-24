import os
import httpx
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Cookie, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from datetime import datetime, timedelta
from src.models import User, SocialLogin, UserSession, Role
from typing import Optional

ENV_PATH = Path(__file__).parent.parent.parent / '.env'
load_dotenv(ENV_PATH)

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
NAVER_REDIRECT_URI = os.getenv('NAVER_REDIRECT_URI')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

router = APIRouter(prefix="/auth/naver", tags=["네이버 소셜로그인 기능"])


# ---------------------------
# 1) 네이버 로그인 URL로 이동
# ---------------------------
@router.get("/login")
async def naver_login():
    state = uuid.uuid4().hex
    naver_url = (
        "https://nid.naver.com/oauth2.0/authorize"
        f"?response_type=code"
        f"&client_id = {NAVER_CLIENT_ID}"
        f"&redirect_uri = {NAVER_REDIRECT_URI}"
        f"&state = {state}"
        f"&auth_type = reprompt"                      # 👈 자동로그인 방지
    )
    return RedirectResponse(url=naver_url)


# ---------------------------
# 2) 네이버 콜백
# ---------------------------
@router.get("/callback")
async def naver_callback(code: str, state: str, db: Session = Depends(get_db)):

    # 1. 토큰 요청
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_params = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "redirect_uri": NAVER_REDIRECT_URI,
        "client_secret": NAVER_CLIENT_SECRET,
        "code": code,
        "state": state,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, params=token_params)

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    expires_in = token_json.get("expires_in", 60 * 60 * 6)

    if not access_token:
        return JSONResponse(
            status_code=400,
            content={"error": "토큰 발급 실패", "details": token_json},
        )

    # 2. 사용자 정보 가져오기
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)

    user_json = user_response.json().get("response", {})
    naver_id = user_json.get("id")
    naver_email = user_json.get("email")
    naver_name = user_json.get("name", "User")
    naver_gender = user_json.get("gender")

    # -----------------------------------------------------------
    # 3. DB 저장 (Kakao랑 동일한 구조)
    # -----------------------------------------------------------
    try:
        oauth_account = (
            db.query(SocialLogin)
            .filter(
                SocialLogin.Provider == "Naver",
                SocialLogin.ProviderUserID == str(naver_id),
            )
            .first()
        )

        user = None
        newly_created = False

        if oauth_account:
            # 기존 사용자 → 기존 세션 삭제
            old_sessions = (
                db.query(UserSession)
                .filter(UserSession.UserID == oauth_account.UserID)
                .all()
            )
            for s in old_sessions:
                db.delete(s)

            oauth_account.UnlinkedAt = None
            user = oauth_account.user
        else:
            # 신규 가입
            user = db.query(User).filter(User.Email == naver_email).first()
            user_role = db.query(Role).filter(Role.Name == "user").first()

            if not user:
                user = User(
                    Email = naver_email if naver_email else f"naver_{naver_id}@no-email.com",
                    Name = naver_name,
                    role = user_role,
                )
                db.add(user)
                db.flush()
                newly_created = True

            new_oauth = SocialLogin(
                UserID = user.UserID,
                Provider = "Naver",
                ProviderUserID = str(naver_id),
                LinkedAt = datetime.now(),
                UnlinkedAt = None,
            )
            db.add(new_oauth)

        db.commit()
        # role 정보 로드
        db.refresh(user)

    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"error": "DB 처리 실패", "details": str(e)}, status_code=500)

    # 4. 세션 DB 저장
    try:
        session_id = str(uuid.uuid4())
        expires_in = int(token_json.get("expires_in", 60 * 60 * 6))
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
        return JSONResponse(
            status_code=500,
            content={"error": "세션 저장 실패", "details": str(e)},
            )

    # 5. 프론트엔드로 이동
    if newly_created:
        html = f"""
        <script>
            localStorage.setItem('isLogin','true');
            localStorage.setItem('isNewUser','true');
            window.location.href='{FRONTEND_URL}/callback?signup=true';
        </script>
        """
    else:
        html = f"""
        <script>
            localStorage.setItem('isLogin','true');
            window.location.href='{FRONTEND_URL}/callback';
        </script>
        """

    response = HTMLResponse(html)

    # 쿠키 설정
    cookie = {
        "httponly": True,
        "secure": False,
        "samesite": "lax",
        "path": "/",
    }

    response.set_cookie("session_id", str(session_id), max_age=60*60*24*30, **cookie)
    response.set_cookie("user_id", str(user.UserID), max_age=60*60*24*30, **cookie)

    # UI용(httponly X)
    response.set_cookie("is_login", "true", httponly=False)

    return response


# ---------------------------
# 3) 로그인 상태 확인
# ---------------------------
@router.get("/me")
async def naver_me(
    user_id: Optional[str] = Cookie(None),
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    if not user_id or not session_id:
        return {"isLoggedIn": False, "user": None}

    # 안전하게 session_id를 UUID로 변환하여 비교합니다.
    try:
        session_uuid = uuid.UUID(session_id)
    except Exception:
        return {"isLoggedIn": False, "user": None}

    session = (
        db.query(UserSession)
        .filter(UserSession.SessionID == session_uuid, UserSession.UserID == int(user_id))
        .first()
    )

    if not session or session.ExpiresAt < datetime.now():
        return {"isLoggedIn": False, "user": None}

    user = db.query(User).filter(User.UserID == int(user_id)).first()
    if not user:
        return {"isLoggedIn": False, "user": None}

    return {
        "isLoggedIn": True,
        "user": {
            "id": user.UserID,
            "name": user.Name,
            "email": user.Email,
            "role": user.role.Name if user.role else "user",
        },
    }


# ---------------------------
# 4) 네이버 로그아웃
# ---------------------------
@router.get("/logout")
async def naver_logout(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    user_id: Optional[str] = Cookie(None),
    naver_access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):

    # 1) 네이버 토큰 무효화
    if naver_access_token:
        try:
            logout_url = "https://nid.naver.com/oauth2.0/token"
            params = {
                "grant_type": "delete",
                "client_id": NAVER_CLIENT_ID,
                "client_secret": NAVER_CLIENT_SECRET,
                "access_token": naver_access_token,
                "service_provider": "NAVER",
            }
            async with httpx.AsyncClient() as client:
                await client.post(logout_url, params = params)
        except:
            pass

    # 쿠키 삭제
    accept = request.headers.get("accept", "")

    def clear(resp):
        opt = {"path": "/", "max_age": 0}
        resp.delete_cookie("session_id", **opt)
        resp.delete_cookie("user_id", **opt)
        resp.delete_cookie("naver_access_token", **opt)
        resp.delete_cookie("naver_refresh_token", **opt)
        resp.delete_cookie("is_login", path="/", max_age = 0, httponly=False)
        return resp

    # DB 세션 삭제
    if session_id:
        try:
            # session_id 쿠키는 문자열이므로 UUID로 변환하여 삭제
            try:
                sid = uuid.UUID(session_id)
                db.query(UserSession).filter(UserSession.SessionID == sid).delete()
            except Exception:
                db.query(UserSession).filter(UserSession.SessionID == session_id).delete()
            db.commit()
        except:
            db.rollback()

    # 소셜 연결 끊기
    if user_id:
        accounts = db.query(SocialLogin).filter(SocialLogin.UserID == int(user_id)).all()
        for a in accounts:
            a.UnlinkedAt = datetime.now()
        db.commit()

    if "application/json" in accept:
        resp = JSONResponse({"message": "logout success"})
        return clear(resp)

    resp = HTMLResponse("<script> alert('로그아웃 되었습니다'); window.location.href='/' </script>")
    return clear(resp)