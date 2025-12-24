"""
Chatbot Router (Streaming Support)

🔥 두 가지 엔드포인트:
- POST /api/chat        : 기존 일괄 응답
- POST /api/chat/stream : 스트리밍 응답 (SSE)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import time
from src.database import get_db
from services.chatbot_service import get_chatbot, initialize_chatbot

router = APIRouter(prefix="/api", tags=["chatbot"])


# ============================================================================
# Request/Response Models
# ============================================================================
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


# ============================================================================
# 기존 엔드포인트 (일괄 응답)
# ============================================================================
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    일괄 응답 방식 채팅
    - 전체 응답 생성 후 한 번에 반환
    """
    start_time = time.time()
    print(f"\n[CHAT] New request: '{request.message}'")
    print(f"[CHAT] User ID: {int(request.user_id)}")
    print("=" * 60)
    
    chatbot = get_chatbot()
    if not chatbot:
        print("[CHAT] ❌ Chatbot not initialized")
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        print("[CHAT] Chatbot ready, starting processing...")
        response = chatbot.chat(
            query=request.message,
            db = db,
            user_id = int(request.user_id)
        )
        
        elapsed = time.time() - start_time
        print(f"[CHAT] ✅ Response generated in {elapsed:.2f}s")
        print(f"[CHAT] Response length: {len(response)} chars")
        
        return ChatResponse(response=response, status="success")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[CHAT] ❌ Error after {elapsed:.2f} seconds")
        print(f"[CHAT] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 🔥 스트리밍 엔드포인트 (SSE)
# ============================================================================
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """
    🚀 스트리밍 방식 채팅 (Server-Sent Events)
    - 토큰 단위로 실시간 전송
    - Claude 같은 UX
    """
    print(f"\n[STREAM] New request: '{request.message}'")
    print(f"[STREAM] User ID: {int(request.user_id)}")
    print("=" * 60)
    
    # ============================================================================
    # 로그인 분기
    # if 로그인:
    #    skill isnon:
    #    - skill이 없다 == 로그인 안했다 == 가입을 안했다 == maching이 0이다 ==>> 매칭률을 안보여준다.
    #    - skill이 아예없으면, 로그인을 해라 -> 가입하면 더 높은 확률로 볼 수 있다! 라고 제안하기.
    # ============================================================================

    chatbot = get_chatbot()
    if not chatbot:
        print("[STREAM] ❌ Chatbot not initialized")
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    async def generate():
        """SSE 형식으로 토큰 스트리밍"""
        try:
            print("[STREAM] Starting generation...")
            token_count = 0
            
            for token in chatbot.chat_stream(
                query = request.message,
                db = db,
                user_id = int(request.user_id)
            ):
                token_count += 1
                
                # 🔥 개행을 이스케이프! (\n → \\n)
                # SSE에서 \n은 메시지 구분자로 인식되므로 이스케이프 필요
                escaped_token = token.replace('\n', '\\n')
                
                yield f"data: {escaped_token}\n\n"
                await asyncio.sleep(0)  # 이벤트 루프에 제어권 반환!
            
            # 완료 신호
            yield "data: [DONE]\n\n"
            print(f"[STREAM] ✅ Complete! {token_count} tokens sent")
            
        except Exception as e:
            print(f"[STREAM] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        }
    )


# ============================================================================
# 상태 확인 엔드포인트
# ============================================================================
@router.get("/chat/status")
async def chat_status():
    """챗봇 상태 확인"""
    chatbot = get_chatbot()
    return {
        "status": "ready" if chatbot else "not_initialized",
        "streaming_supported": True
    }
