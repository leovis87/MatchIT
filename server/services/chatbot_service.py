"""
RAG Chatbot Service (Hybrid Streaming Version)

🔥 Hybrid 방식:
- 채용공고/부트캠프 데이터: 코드로 확실하게 포맷팅
- AI: 인사말 + 코멘트 담당
- 스트리밍으로 자연스러운 UX
"""
import anthropic
import sys
import io
import os
import re
import torch
import logging
import time
from typing import Dict, List, Optional, Generator
from datetime import datetime
from threading import Thread
from utils.search_vector import (search_jobs_by_vector,
                                search_bootcamps_by_vector)
from utils.db_queries import (get_user_skills,
                              extract_profile)
from utils.set_model import (_format_job_card,
                             _format_bootcamp_card)
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    BitsAndBytesConfig, TextIteratorStreamer)
from pgvector.sqlalchemy import Vector
from peft import PeftModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.DEBUG,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'test_logging.log'
)

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print(f'\n    🛠️ Cuda_is: {torch.cuda.is_available()}')

# ===== LLM model selector =====
Use_Claude = False

# ============================================================================
# Clude API_key 호출
# anthropic.Anthropic() => API 클라이언트 생성
# ============================================================================
client = anthropic.Anthropic(
    api_key = os.environ.get("ANTHROPIC_API_KEY")
)


# ============================================================================
# Claude models - claude API
# models["sonnet"] 으로 모델명 로드
# ============================================================================
models = {
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
    "opus": "claude-opus-4-20250514"
}

# 저렴이: models['haiku']
# 기본: models['sonnet']


# ============================================================================
# SBERT 모델 (CPU) - 사용자 query vectorize
# ============================================================================
print("\n    📦 Loading SBERT model (CPU)...")
print("\n    ✅ SBERT model loaded on CPU!")


# ============================================================================
# Conversation History Manager
# ============================================================================
class ConversationHistory:
    def __init__(self,
                 max_history: int = 5):
        self._history: Dict[str, List[Dict]] = {}
        self.max_history = max_history
    
    def add_message(self,
                    user_id: str,
                    role: str,
                    content: str):
        if user_id not in self._history:
            self._history[user_id] = []
        self._history[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        if len(self._history[user_id]) > self.max_history * 2:
            self._history[user_id] = self._history[user_id][-self.max_history * 2:]
    
    def get_history(self, user_id: str) -> List[Dict]:
        return self._history.get(user_id, [])
    
    def clear_history(self, user_id: str):
        if user_id in self._history:
            del self._history[user_id]

conversation_manager = ConversationHistory()


# ============================================================================
# RAG Chatbot (Hybrid Streaming Version)
# ============================================================================
class RAGChatbot:
    """
    EXAONE 기반 Hybrid 챗봇 + Claude 기반 Hybrid 챗봇
    
    🚀 특징:
        - 데이터: 코드로 확실하게 포맷팅 (채용공고, 부트캠프)
        - AI: 인사말, 코멘트, 마무리만 생성
        - 스트리밍으로 자연스러운 UX
    """
    def __init__(
        self,
        claude_model_name: str = models['haiku'],
        client: str = client,
        base_model_name: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
        lora_model_path: str = "ai/models/checkpoint-460",
        use_4bit: bool = True
    ):
        print("\n    🚀 Initializing RAG Chatbot (Hybrid Streaming)...")
    
        # ===== Local or API selector =====
        # 분기 -> True: Claude
        #        False: Local Model
        # =================================
        if Use_Claude:
            print("\n    ✅ 선택 모델: Claude API\n")
            # ===== Claude API  =====
            # api_key loading
            self.client = client

            # model name select
            self.claude_model_name = claude_model_name
            self.model = None
            print(f"\n    🤖: {self.claude_model_name} model loaded!\n")

        elif not Use_Claude:
            # ===== Local model (EXAONE + LoRA) =====
            print(f"\n    ✅ 선택 모델: Local model\n")
            os.makedirs("./offload",
                        exist_ok = True)
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                trust_remote_code = True
            )
            
            bnb_config = None
            if use_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit = True,
                    bnb_4bit_compute_dtype = torch.float16,
                    bnb_4bit_quant_type = 'nf4',
                    bnb_4bit_use_double_quant = True,
                )
            
            print(f"\n   📥 Loading: {base_model_name}")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                quantization_config = bnb_config,
                device_map = 'auto',
                trust_remote_code = True,
                low_cpu_mem_usage = True,
                max_memory = {0: "6GiB", "cpu": "16GiB"},
                offload_folder = "./offload",
            )
            print("\n    ✅ Base model loaded!\n")
            print(f"\n    📥 Loading: {lora_model_path}")

            if lora_model_path and os.path.exists(lora_model_path):
                print(f"\n    📦 Loading LoRA: {lora_model_path}")
                self.model = PeftModel.from_pretrained(base_model, lora_model_path)

            else:
                self.model = base_model
            print("\n    ✅ Trained model loaded!\n")
            print("\n    ✅ Hybrid Streaming Chatbot ready!\n")

    # ========================================================================
    # Local model용 generate
    # model generate 함수
    # ========================================================================
    def generate(self,
                 prompt: str,
                 max_tokens: int = 128) -> str:
        """LLM 호출 메서드"""
        inputs = self.tokenizer(prompt, return_tensors = 'pt').to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens = max_tokens,
            do_sample = True,
            temperature = 0.7,
            top_p = 0.9
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens = True)
    
    def analyze_skill_gap(self,
                          user_skills: List[str],
                          job_skills: List[str]) -> Dict:
        if not job_skills:
            return {
                'match_rate': 100,
                'matched': [],
                'missing': [],
                'gap_level': 'none'
                }
        
        user_lower = [s.lower() for s in user_skills]
        # matched = [s for s in job_skills if s.lower() in user_lower]
        # 사용자 스킬 기준으로 매칭된 것을 반환
        job_lower = [s.lower() for s in job_skills]
        matched = [s for s in user_skills if s.lower() in job_lower]
        missing = [s for s in job_skills if s.lower() not in user_lower]
        rate = len(matched) / len(job_skills) * 100 if job_skills else 100
        
        level = 'minor' if rate >= 80 else 'moderate' if rate >= 50 else 'major'
        
        logging.debug(f"[DEBUG] user_skills: {user_skills}")
        logging.debug(f"[DEBUG] job_skills: {job_skills}")
        logging.debug(f"[DEBUG] matched: {matched}")
        logging.debug(f"[DEBUG] missing: {missing}")
        logging.debug(f"[DEBUG] rate: {rate}")

        return {
            'match_rate': round(rate),
            'matched': matched,
            'missing': missing,
            'gap_level': level
            }


    # ========================================================================
    # 🔥 AI 프롬프트 (짧게! 인사/코멘트만)
    # ========================================================================
    def _build_greeting_prompt(self, query: str,
                               user_skills: List[str],
                               job_count: int) -> str:
        """
        인사말 생성용 짧은 프롬프트
            기존: 너무 모호한 지시.
            개선: 명확한 지시.
        """
        skills_str = ', '.join(user_skills) if user_skills else '스킬 미입력'
        
        return f"""[|system|]너는 MatchIT 취업 도우미야. 
정중하고 친근하게 인사해. 2문장으로만 답해.[|endofturn|]
[|user|]사용자가 "{query}"라고 검색한 내용을 찾아봤다고 안내해 줘
1. 반가운 말투로 인사를 해 줘
2. 사용자가 원하는 답을 친절하고 정확하게 안내해 주겠다고 말해 줘
3. 회사명이나 스킬, 구인구직 공고 내용을 안내하지 말아줘
2문장으로만 자연스럽게 답해![|endofturn|]
[|assistant|]"""

#     def _build_comment_prompt(self, job: Dict, gap: Dict) -> str:
#         """채용공고별 코멘트 생성용 짧은 프롬프트"""
#         return f"""[|system|]너는 취업 도우미야. 이 채용공고에 대해 2~4문장으로 각 공고에 대한 평가와 부족한 스킬별 학습 방법을 코멘트 해줘.[|endofturn|]
# [|user|]회사: {job['company']}
# 직무: {job['title']}
# 매칭률: {gap['match_rate']}%
# 부족 스킬: {', '.join(gap['missing'][:2]) if gap['missing'] else '없음'}
# 이 공고를 추천해 준 이유에 대해서 코멘트 해줘![|endofturn|]
# [|assistant|]"""

#     def _build_closing_prompt(self, missing_skills: List[str], has_bootcamps: bool) -> str:
#         """마무리 멘트 생성용 짧은 프롬프트 - 간결하게"""
        
#         return f"""[|system|]너는 MatchIT 취업 도우미야.
# 반말로 짧게 응원해. 반드시 1문장으로만![|endofturn|]
# [|user|]사용자에게 응원 한마디 해줘.
# 1문장으로만! 이모지 1개만 써![|endofturn|]
# [|assistant|]"""

    def _build_recommendation_reason_prompt(self, 
                                            query: str,
                                            user_skills: List[str],
                                            jobs: List[Dict],
                                            overall_gap: Dict,
                                            bootcamps: List[Dict]) -> str:
        """
        추천 이유 생성용 프롬프트
            - 기존: 부정적인 표현 ("너 이거 부족해")
            - 개선: 긍정적인 표현 ("이거 배우면 더 좋아!")
        """
        # # 사용자 이름
        # user_name_str = 

        # 사용자 스킬
        user_skills_str = ', '.join(user_skills) if user_skills else '아직 입력 안 됨'
        logging.debug(f'[User_skills]: {user_skills_str}')

        # 배우면 좋은 스킬 (상위 3개)
        missing_skills = overall_gap.get('missing', [])[:3]
        missing_skills_str = ', '.join(missing_skills) if missing_skills else '없음'
        logging.debug(f'[missing_skills]: {missing_skills_str}')

        # 회사명 (최대 3개)
        company_names = [job.get('company', '')[:10] for job in jobs[:2]]
        companies_str = ', '.join(company_names) if company_names else "여러 회사"
        logging.debug(f'[missing_skills]: {companies_str}')
        
        # 부트캠프 이름
        # bootcamp_name = ''
        # if bootcamps and len(bootcamps) > 0:
        #     bootcamp_name = bootcamps[0].get('name', '')[:40]
        
        return f"""[|system|]너는 MatchIT 커리어 전문 코치야. 너의 이름은 MatchIT 챗봇이야. 5문장으로 정중하고 친절하게 자연스러운 말투로 말해.[|endofturn|]
[|user|]아래 예시처럼 5문장으로 조언해줘.

[정보]
사용자 스킬: {user_skills_str}
추천 회사: {companies_str}
배우면 좋을 스킬: {missing_skills_str}

[예시]
1. 자연스러운 말투로 사용자 스킬을 칭찬해줘
2. 추천 회사에서 원하는 스킬을 말해줘
3. 배우면 좋을 스킬도 몇가지 말해줘
4. 마지막으로 응원의 메시지
5. 정보가 없는 내용은 추측해서 만들거나 포함하지 말아줘
6. 인사할 때, 사용자의 이름을 추가하지마

"{user_skills_str}" 스킬 좋아! {companies_str} 같은 회사들이 {missing_skills_str}도 원해. {missing_skills_str} 중 하나 배우면 선택지가 넓어져! 위 부트캠프도 참고해봐, 화이팅!

회사명이나 스킬만을 말하지 말고 자연스럽게 말해![|endofturn|]
[|assistant|]"""

    # ========================================================================
    # 🔥 AI 텍스트 생성 (짧은 응답용)
    # ========================================================================
    def _generate_short_response(self,
                                 prompt: str,
                                 max_tokens: int = 100) -> str:
        """짧은 AI 응답 생성 (스트리밍 아님)"""
        inputs = self.tokenizer(
            prompt,
            return_tensors = "pt",
            truncation = True,
            max_length = 512
        ).to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens = max_tokens,
                temperature = 0.7,              # 높을수록 더 다양하고 창의적인 출력.
                do_sample = True,               # True: 확률 분포에서 무작위로 샘플링(다양성 증가)
                top_p = 0.9,                    # 확률 누적합이 0.9가 될 때까지 상위 토큰만 후보로 두고 샘플링. 나머지 무시
                repetition_penalty = 1.1,       # 같은 단어나 구절이 반복되는 것을 억제. 1.1이상 => the the the... 방지
                pad_token_id = self.tokenizer.eos_token_id,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens = False)
        
        # [|assistant|] 이후 텍스트만 추출
        if "[|assistant|]" in response:
            response = response.split("[|assistant|]")[-1]
        
        # 종료 토큰 제거
        if "[|endofturn|]" in response:
            response = response.split("[|endofturn|]")[0]
        
        return response.strip()

    # ========================================================================
    # 🔥 AI 텍스트 생성 (streaming ver.)
    # ========================================================================
    def _generate_stream_response(self, prompt: str, max_tokens: int = 100) -> Generator[str, None, None]:
        """AI 응답을 토큰 단위로 스트리밍"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(self.model.device)
        
        # 스트리머 생성
        streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=False)
        
        # 별도 스레드에서 생성
        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens,
            "temperature": 0.7,                 # 높을수록 더 다양하고 창의적인 출력.
            "do_sample": True,                  # True: 확률 분포에서 무작위로 샘플링(다양성 증가)
            "top_p": 0.9,                       # 확률 누적합이 0.9가 될 때까지 상위 토큰만 후보로 두고 샘플링. 나머지 무시
            "repetition_penalty": 1.1,          # 같은 단어나 구절이 반복되는 것을 억제. 1.1이상 => the the the... 방지
            "pad_token_id": self.tokenizer.eos_token_id,
            "streamer": streamer,
        }
        
        thread = Thread(target = self.model.generate, kwargs = generation_kwargs)
        thread.start()
        
        # 토큰 단위로 yield
        started = False
        for token in streamer:
            # [|assistant|] 이후부터 출력
            if "[|assistant|]" in token:
                started = True
                token = token.split("[|assistant|]")[-1]
            
            if started:
                # 종료 토큰이면 중단
                if "[|endofturn|]" in token:
                    token = token.split("[|endofturn|]")[0]
                    if token:
                        yield token
                    break
                yield token
        
        thread.join()

    # ========================================================================
    # 🔥 Hybrid 스트리밍 Chat (핵심!)
    # ========================================================================
    def chat_stream(self, query: str,
                    db: Session,
                    user_id: str = 2) -> Generator[str, None, None]:
        """
        chat_stream() 흐름:

        1. AI 인사말 (LLM 호출 1회)
        2. 채용공고 카드 3개 (코드로 생성, embedding 유사도 길이)
        3. 스킬 분석 (코드로 생성, LLM 없음) -> 삭제
        4. 부트캠프 카드 2개 (코드로 생성, embedding 유사도 길이)
        4.5 추천 이유 (LLM 호출 1회) ← 추가!
        5. AI 마무리 (LLM 호출 1회) -> 삭제

        총 LLM 호출: 2회 (인사말 + 추천이유 1회)
        """
        try:
            # 0. LangChain 도입 비교를 위해 시간 측정
            start_time = time.perf_counter()

            # 1. 프로필 추출 & 검색
            profile = extract_profile(query)
            print(f"[hybrid] Profile: {profile}")
            
            logging.debug(f'[USER_ID_check] {user_id}')

            # 2. 사용자 스킬
            user_skills = []
            if user_id:
                try:
                    logging.debug(f'[USER_ID] {user_id}')
                    skills = get_user_skills(db, int(user_id))

                    logging.debug(f'[USER_skills] {skills}')
                    user_skills.extend(skills)

                    logging.debug(f'[USER_skills_extended] {user_skills}')

                except:
                    pass

            if profile['skills']:
                for s in profile['skills']:
                    if s not in user_skills:
                        user_skills.append(s)

            logging.debug(f'[DEBUG] User스킬 확인: {user_skills}')
            
            # 3. 채용공고 검색
            # jobs = self.search_jobs(db, profile, limit=3)
            jobs = search_jobs_by_vector(db, query, limit = 20) # 여유있게 지정.

            print(f"[hybrid] Found {len(jobs)} jobs")

            # 추가: matched 스킬이 1개 이상인 것만 필터링
            filtered_jobs = []
            for job in jobs:
                job_gap = self.analyze_skill_gap(user_skills, job['skills'])
                if job_gap['matched']:  # matched가 있으면 == 1개 이상이면
                    filtered_jobs.append(job)
                if len(filtered_jobs) >= 3: # 최대 3개
                    break

            jobs = filtered_jobs
            
            if not jobs:
                yield "음... 조건에 맞는 공고를 못 찾았어 😅\n\n다른 스킬이나 지역으로 검색해볼까?"
                return
            
            # 4. 스킬 갭 분석
            all_skills = list(set(s for j in jobs for s in j.get('skills', [])))
            overall_gap = self.analyze_skill_gap(user_skills, all_skills)
            
            # 5. 부트캠프 검색
            bootcamps = []
            if overall_gap['missing']:
                # LLM 직접 확인&추천
                # bootcamps = self.recommend_bootcamps(query, db, limit = 2)

                # Vector cosine 유사도 query 추천(job과 같음)
                # bootcamps = self.search_bootcamps_by_vector(db, query, limit = 2) 
                
                # query에서 부족한 스킬로 부트캠프 검색
                missing_skills_str = ', '.join(overall_gap['missing'][:4])
                missing_skills_query = f'주요스킬: {missing_skills_str}. 개발자 교육 부트캠프'

                logging.debug(f'[DEBUG] Bootcamp search query: {missing_skills_query}') # 디버깅 -> logging

                bootcamps = search_bootcamps_by_vector(db, missing_skills_query, limit = 2)
            
            
            # ═══════════════════════════════════════════════════════════════
            # 🔥 Hybrid 응답 시작!
            # ═══════════════════════════════════════════════════════════════
            
            full_response = ""
            
            # ─────────────────────────────────────────────────────────────
            # Part 1: AI 인사말
            # ─────────────────────────────────────────────────────────────
            greeting_prompt = self._build_greeting_prompt(query, user_skills, len(jobs))

            # 한꺼번에 출력
            greeting = self._generate_short_response(greeting_prompt, max_tokens = 100)

            # 인사말
            # 하기 뒤아래 부분을 추가하므로써 프론트에서 해당 부분이 AI 응답 부분인걸 인식!!!
            yield "<!-- AI_GREETING -->\n"
            yield greeting
            # streaming 방식 출력 (token 단위 출력)
            # for token in self._generate_stream_response(greeting_prompt, max_tokens = 80):
            #     yield token
            yield "\n<!-- /AI_GREETING -->\n"
            full_response += greeting + "\n\n"
            
            # ─────────────────────────────────────────────────────────────
            # Part 2: 채용공고 카드 (코드로 확실하게!)
            # ─────────────────────────────────────────────────────────────
            jobs_header = f"\n\n📋 **검색된 채용공고 {len(jobs)}건**\n\n"
            yield "<!-- JOB_CARDS -->\n"
            yield jobs_header
            full_response += jobs_header
            
            for i, job in enumerate(jobs):
                print(f"[DEBUG] Job {i+1}: {job['company']}")
                job_gap = self.analyze_skill_gap(user_skills, job['skills'])
                
                # 🔥 직접 문자열 생성 (함수 호출 대신)
                skills_str = ', '.join(job['skills'][:4]) if job['skills'] else '스킬 미기재'
                # match_emoji = "🟢" if job_gap['match_rate'] >= 70 else "🟡" if job_gap['match_rate'] >= 40 else "🔴"
                
                # URL 링크
                company_display = job['company']
                if job.get('url'):
                    company_display = f"[{job['company']}]({job['url']})"
                
                # 🔥 각 줄을 개별 yield로!
                yield f"🏢 {company_display}\n"
                yield f"📌 {job['title']}\n"
                yield f"📍 {job['location']} | 💼 {job['experience']} | 💰 {job['salary']}\n"
                yield f"🛠️ {skills_str}\n"
                
                # 부정적인 표현으로 UX 저하. 교체
                # match_line = f"│ {match_emoji} 매칭률 {job_gap['match_rate']}%"
                # if job_gap['missing']:
                #     match_line += f" (부족: {', '.join(job_gap['missing'][:2])})"
                # yield match_line + "\n"

                # 🔥 긍정적 표현으로 변경!
                if job_gap['matched']:
                    matched_str = ', '.join(job_gap['matched'][:3])  # 최대 3개만 표시
                    match_line = f"✅ {matched_str} 활용 가능"
                else:
                    match_line = f"📌 새로운 도전 기회!"
                yield match_line + "\n"

                # 🆕 카드 사이 구분선 추가!
                yield "\n───────────────────\n\n"

                # full_response 업데이트
                card = f"""
🏢 {company_display}
📌 {job['title']}
📍 {job['location']} | 💼 {job['experience']} | 💰 {job['salary']}
🛠️ {skills_str}
"""
                if job_gap['matched']:
                    matched_str = ', '.join(job_gap['matched'][:3])  # 최대 3개만 표시
                    match_line = f"✅ {matched_str} 활용 가능"
                else:
                    match_line = f"📌 새로운 도전 기회!"
                full_response += card
                
                print(f"[DEBUG] Card {i+1} yielded")
            yield"<!-- /JOB_CARDS -->\n"
            
            # ─────────────────────────────────────────────────────────────
            # Part 3: 스킬 분석
            # ─────────────────────────────────────────────────────────────
            # 부정적인 표현 -> UX 저하 -> 주석처리
            # if overall_gap['missing']:
            #     yield f"\n📊 **스킬 분석**\n"
            #     yield f"• 매칭률: {overall_gap['match_rate']}%\n"
            #     yield f"• 부족한 스킬: {', '.join(overall_gap['missing'][:4])}\n"
            #     full_response += f"\n📊 **스킬 분석**\n• 매칭률: {overall_gap['match_rate']}%\n• 부족한 스킬: {', '.join(overall_gap['missing'][:4])}\n"
            
            # ─────────────────────────────────────────────────────────────
            # Part 4: 부트캠프 추천 (있으면)
            # ─────────────────────────────────────────────────────────────
            if bootcamps:
                yield "<!-- BOOTCAMP_CARDS -->\n"
                yield f"\n\n📚 **추천 부트캠프**\n\n"
                full_response += f"\n\n📚 **추천 부트캠프**\n\n"
                
                # recommend_bootcamps == bootcamps에서 (bc, score, reason) 반환
                # cards == List(card, card, ...)
                # card == Dict('name': name_display,
                #              'subtitle': f'점수: {score}',
                #              'description': reason,
                #              'extra': {'category': bc.get('category_name', ''),
                #                        'link': bc.get('detail_url', '')
                #                                원본 url 그대로 저장)
                for card in bootcamps:
                    """부트캠프 추천 카드 포맷팅"""
                    cost_emoji = "🆓" if "국비" in card['extra'].get('cost_type', '') else "💳"

                    # 이름을 Markdown 링크로 변환
                    # URL이 있으면 Markdown 링크
                    name_display = card.get('name', '부트캠프명 없음')
                    if card['extra'].get('link'):
                        name_display = f"[{name_display}]({card['extra']['link']})"

                    logging.debug(f'[DEBUG] {name_display}')

                    bc_card = f"""
🎓 {name_display}
🏫 {card['extra'].get('institute', '기관 미기재')} | {cost_emoji} {card['extra'].get('cost_type', '')} | {card['extra'].get('online_offline', '')}
📍 {card['extra'].get('location', '온라인')}
✒️ {card.get('description', '')}
"""
                    logging.debug(f'[DEBUG] {bc_card}')

                    # 스트리밍 출력
                    yield bc_card + "\n"
                    yield "\n───────────────────\n\n"

                    # 전체 응답 누적
                    full_response += bc_card + "\n"

                yield "<!-- /BOOTCAMP_CARDS -->\n"
                # ─────────────────────────────────────────────────────────────
                # Part 4.5: 부트캠프 추천 이유
                # ─────────────────────────────────────────────────────────────
                reason_prompt = self._build_recommendation_reason_prompt(
                    query, user_skills, jobs, overall_gap, bootcamps  # overall_gap 추가!
                )

                # 한꺼번에 출력
                recommendation_reason = self._generate_short_response(reason_prompt, max_tokens = 350)

                yield "<!-- AI_ROADMAP -->\n"
                yield f"\n💡 **추천 스킬 로드맵**\n"

                # streaming 방식 출력 (token 단위로 출력)
                for token in self._generate_stream_response(reason_prompt, max_tokens = 350):
                    yield token
                # yield f"{recommendation_reason}\n"
                yield "<!-- /AI_ROADMAP -->\n"

                full_response += f"\n💡 **추천 스킬 로드맵**\n{recommendation_reason}\n"

            
            # ─────────────────────────────────────────────────────────────
            # Part 5: AI 마무리
            # ─────────────────────────────────────────────────────────────
            # 히스토리 저장
            if user_id:
                conversation_manager.add_message(user_id, "user", query)
                conversation_manager.add_message(user_id, "assistant", full_response[:200])
            
            print(f"[hybrid] Complete! Length: {len(full_response)}")
            
            # 0. 측정 종료 시점
            end_time = time.perf_counter()

            elapsed_time = end_time - start_time
            logging.info(f'[TIME] 총 소요 시간: {elapsed_time:.4f} 초')
            
        except Exception as e:
            print(f"[hybrid] Error: {e}")

            import traceback
            traceback.print_exc()
            yield "앗, 오류가 생겼어 😓 다시 시도해줄래?"


    # ========================================================================
    # 기존 chat 함수 (일괄 응답 - 호환성 유지)
    # ========================================================================
    def chat(self, query: str, db: Session, user_id: str = None) -> str:
        """일괄 응답 방식 (기존 호환)"""
        result = ""
        for token in self.chat_stream(query, db, user_id):
            result += token
        return result

# ============================================================================
# Global Instance
# ============================================================================
chatbot: Optional[RAGChatbot] = None

def initialize_chatbot(
    claude_model_name : Optional[str] = models['haiku'],
    base_model_name: Optional[str] = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
    lora_model_path: Optional[str] = "ai/models/checkpoint-460"
):
    global chatbot
    try:
        chatbot = RAGChatbot(
            claude_model_name = claude_model_name,
            base_model_name = base_model_name,
            lora_model_path = lora_model_path,
            use_4bit = True
        )
        return True
    
    except Exception as e:
        print(f"\n    ❌ Init failed: {e}\n")
        import traceback

        traceback.print_exc()
        return False


def get_chatbot() -> Optional[RAGChatbot]:
    return chatbot
