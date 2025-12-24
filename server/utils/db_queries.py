"""
구성

1. DB column과 연결 함수
    - 
"""
from typing import List, Dict, Tuple, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.DEBUG,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'db_queries_logging.log'
)

SBERT_MODEL = SentenceTransformer(
    'jhgan/ko-sbert-nli',
    device = 'cpu'  # VRAM 절약을 위해 CPU 사용
)

# ========================================================================
# DB 조회 함수들
# ========================================================================
def get_user_skills(db: Session,
                    user_id: int) -> List[str]:
    from src.models import User
    try:
        user = db.query(User).filter(User.UserID == user_id).first()
        logging.debug(f'[DEBUG] user 객체 확인: {user}')
        logging.debug(f'[DEBUG] user.skill 객체 확인: {user.skills}')
        if user and user.skills:
            return [skill.SkillName for skill in user.skills]
    except Exception as e:
        logging.error(f"[ERROR] 에러: {e}")
    return []

def extract_profile(query: str) -> Dict:
    query_lower = query.lower()
    profile = {'skills': [], 'location': None, 'experience': None}
    
    skill_mapping = {
        'python': 'Python', '파이썬': 'Python',
        'java': 'Java', '자바': 'Java',
        'javascript': 'JavaScript', 'js': 'JavaScript',
        'react': 'React', '리액트': 'React',
        'fastapi': 'FastAPI', 'git': 'git',
        'github': 'github', 'ai': 'ai',
        '에이아이': 'ai', 'deep-learning': 'Deep-Learning',
        'Deep-Learning': 'Deep-Learning', 'C': 'C',
        'C++': 'C++', 'C#': 'C#',
        'vue': 'Vue', 'django': 'Django',
        'spring': 'Spring',
        'node': 'Node.js', 'typescript': 'TypeScript',
        'postgresql': 'PostgreSQL', 'mysql': 'MySQL',
        'docker': 'Docker', 'kubernetes': 'Kubernetes',
        'aws': 'AWS', 'machine learning': 'Machine_Learning',
        '머신러닝': 'Machine_Learning', 'ml': 'Machine_Learning',
    }
    
    for key, normalized in skill_mapping.items():
        if key in query_lower and normalized not in profile['skills']:
            profile['skills'].append(normalized)
    
    regions = {'서울': '서울', '부산': '부산', '대구': '대구', '인천': '인천',
                '경기': '경기', '대전': '대전', '광주': '광주', '제주': '제주'}
    for key, value in regions.items():
        if key in query_lower:
            profile['location'] = value
            break
    
    if any(w in query_lower for w in ['신입', 'junior', '주니어', '초보']):
        profile['experience'] = '신입'
    elif any(w in query_lower for w in ['경력', 'senior', '시니어']):
        profile['experience'] = '경력'
    
    return profile

def get_query_embedding(query: str) -> list:
    '''
    사용자 쿼리를 768차원 벡터로 변환
    
    비유: 사용자의 질문을 "숫자 지문"으로 바꾸는 과정
        이 지문으로 DB에서 비슷한 지문을 가진 공고를 찾음
    
    Args:
        query: 사용자 질문 (예: "Python 백엔드 개발자 채용")
    
    Returns:
        list[float]: 768차원 벡터 (숫자 리스트)
    '''
    embedding = SBERT_MODEL.encode(query)
    return embedding.tolist()

def preprocess_query_for_embedding(query: str) -> str:
    '''
    사용자 쿼리를 임베딩 검색에 최적화된 형태로 변환
    
    비유: 도서관 검색 시스템에 맞게 검색어 다듬기
        "python 신입 채용" → "제목: python 개발자. 경력: 신입."
    
    Args:
        query: 원본 사용자 쿼리
    
    Returns:
        str: 전처리된 쿼리
    '''
    # 프로필 추출 (기존 함수 활용)
    profile = extract_profile(query)
    
    # 임베딩 텍스트 형식과 유사하게 구성
    parts = []
    
    if profile['skills']:
        parts.append(f"주요스킬: {', '.join(profile['skills'])}")
    
    if profile['experience']:
        parts.append(f"경력: {profile['experience']}")
    
    if profile['location']:
        parts.append(f"지역: {profile['location']}")
    
    # 원본 쿼리도 포함 (의미 보존)
    parts.append(query)
    
    return '. '.join(parts)