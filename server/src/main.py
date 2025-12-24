from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time
import logging
import os
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    jwt_login, google, kakao, naver,
    comparison, users, bootcamper,
    search, skills, meta, jobposts,
    job_categories, admin, chatbot_streaming)

app = FastAPI(title = "MatchIT Backend")

# 개발용 CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
    "http://0.0.0.0:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(jwt_login.router)
app.include_router(google.router)
app.include_router(kakao.router)
app.include_router(naver.router)
app.include_router(comparison.router)
app.include_router(users.router)
app.include_router(bootcamper.router)
app.include_router(jobposts.router)
app.include_router(search.router)
app.include_router(skills.router)
app.include_router(meta.router)
app.include_router(chatbot_streaming.router)
app.include_router(job_categories.router)
app.include_router(admin.router)

logger = logging.getLogger(__name__)


@app.on_event("startup")
def on_startup():
    # Wait for DB to be ready (simple retry loop). This prevents immediate
    # OperationalError when the DB container is still initializing.
    from src.database import engine
    max_retries = 10
    delay = 1  # seconds

    # DB 연결 retry
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect():
                logger.info(f"✅ DB 연결 성공 (attempt {attempt}/{max_retries})")
                break
        except Exception as e:
            logger.warning(f"⚠️ DB 연결 실패 (attempt {attempt}/{max_retries}): {e}")
            time.sleep(delay)
    else:
        logger.error("DB did not become ready after %s attempts", max_retries)

    # 챗봇 초기화 with retry
    lora_model_path = os.getenv("LORA_MODEL_PATH")
    # hf_token = os.getenv("HF_TOKEN")

    if lora_model_path:
        logger.info("🤖 챗봇 초기화 시작...")

        # # HF_TOKEN 확인
        # if not hf_token:
        #     logger.error("❌ HF_TOKEN 환경변수가 설정되지 않았습니다!")
        #     logger.error("   docker-compose.yml에서 HUGGINGFACE_HUB_TOKEN을 확인하세요.")
        #     return
        # else:
        #     logger.info(f"✅ HF_TOKEN 확인 완료 (길이: {len(hf_token)} chars)")

        # 챗봇 초기화 retry (최대 3번)
        chatbot_max_retries = 3
        chatbot_delay = 5  # seconds

        for attempt in range(1, chatbot_max_retries + 1):
            try:
                logger.info(f"🔄 챗봇 초기화 시도 {attempt}/{chatbot_max_retries}...")
                from services.chatbot_service import initialize_chatbot
                success = initialize_chatbot(lora_model_path)

                if success:
                    logger.info("✅ 챗봇 초기화 완료!")
                    break
                else:
                    logger.warning(f"⚠️ 챗봇 초기화 실패 (attempt {attempt}/{chatbot_max_retries})")
                    if attempt < chatbot_max_retries:
                        logger.info(f"⏳ {chatbot_delay}초 후 재시도...")
                        time.sleep(chatbot_delay)

            except Exception as e:
                logger.error(f"❌ 챗봇 초기화 오류 (attempt {attempt}/{chatbot_max_retries}): {e}")
                import traceback
                logger.error(traceback.format_exc())

                if attempt < chatbot_max_retries:
                    logger.info(f"⏳ {chatbot_delay}초 후 재시도...")
                    time.sleep(chatbot_delay)
        else:
            logger.error(f"❌ 챗봇 초기화 최종 실패 ({chatbot_max_retries}번 시도 후)")
            logger.error("   서버는 계속 실행되지만 챗봇 기능은 비활성화됩니다.")
    else:
        logger.info("ℹ️ LORA_MODEL_PATH 미설정 - 챗봇 기능 비활성화")

@app.get("/")
def root():
    return {"message": "MatchIT Backend is running"}

@app.get("/health")
def health_check():
    """Docker health check endpoint"""
    return {"status": "healthy", "service": "MatchIT Backend"}

# 로그인 페이지
@app.get('/login', response_class=HTMLResponse)
def login():
    return"""
    <html>
        <body>
            <div>
                <h3>구글 로그인</h3>
                <a href='/auth/google'>
                    <img src='images/google_login.png'
                    alt='구글 로그인' style='width: 123px; cursor: pointer;'></img>
                </a>
            </div>
            <div>
                <h3>카카오 로그인</h3>
                <a href='/auth/kakao'>
                    <img src='images/kakao_login.png'
                    alt='카카오 로그인' style='width: 123px; cursor: pointer;'></img>
                </a>
            </div>
            <div>
                <h3>네이버 로그인</h3>
                <a href='/auth/naver'>
                    <img src='images/naver_login.png'
                    alt='네이버 로그인' style='width: 123px; cursor: pointer;'></img>
                </a>
            </div>
        </body>
    </html>
    """

@app.get("/auth/kakao/callback")
async def kakao_callback(code: str | None = None, error: str | None = None):
    print("kakao_callback:", code, error)
