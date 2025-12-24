"""
구성

1. embedding vector화 검색 함수
    - 
"""
from typing import List, Dict, Tuple, Optional, Union
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Session
from utils.db_queries import (get_query_embedding,
                              preprocess_query_for_embedding)
import logging

logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.DEBUG,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'search_vector_logging.log'
)

def search_jobs_by_vector(db: Session,
                            query: str,
                            limit: int = 3) -> List[Dict]:
    '''
    벡터 유사도 기반 채용공고 검색
    
    비유: 도서관에서 책 찾기
        - 기존 방식: 제목에 "Python" 단어가 있는 책 찾기 (키워드)
        - 벡터 방식: "Python 개발" 느낌과 비슷한 책 찾기 (의미)
    
    Args:
        db: SQLAlchemy 세션
        query: 사용자 질문
        limit: 반환할 결과 수 (기본값: 3)
    
    Returns:
        List[Dict]: 채용공고 리스트 (유사도 높은 순)
    '''
    from src.models import JobPost  # 순환 import 방지
    
    # 1. 쿼리를 벡터로 변환
    # query_vector = self.get_query_embedding(query)
    processed_query = preprocess_query_for_embedding(query)
    logging.debug(f'[VECTOR] Processed query: {processed_query}') # DEBUG용
    query_vector = get_query_embedding(processed_query)
    
    # 2. cosine 유사도로 검색 (pgvector: <=> 연산자 = cosine 거리)
    #    거리가 작을수록 유사도가 높음 → order by 오름차순
    #    임계값 0.5 초과만 추천
    jobs = db.query(JobPost).filter(
        JobPost.Embeded.isnot(None),  # 벡터가 있는 것만
        # JobPost.Embeded.cosine_distance(query_vector) < 0.1 # 임시로 임계값 없앰
    ).order_by(
        JobPost.Embeded.cosine_distance(query_vector)  # 거리 기준 정렬
    ).limit(limit).all()

    # 유사도 debug용 코드
    # for job in jobs:
    #     distance = db.query(
    #         JobPost.Embeded.cosine_distance(query_vector)
    #     ).filter(JobPost.Id == job.Id).scalar()
    #     logging.debug(f"[VECTOR] {job.Title}: distance={distance}")

    for job in jobs:
        logging.debug(f"[VECTOR] Result: {job.Title} | Company: {job.CompanyName}")
    
    # 3. 기존 search_jobs()와 동일한 형식으로 반환
    results = []
    for job in jobs:
        results.append({
            'company': job.CompanyName or '회사명 미공개',
            'title': job.Title or '직무명 없음',
            'location': job.Location or '위치 미정',
            'experience': job.ExperienceRequirement or '무관',
            'salary': job.Salary or '협의',
            'skills': [s.SkillName for s in job.skills] if job.skills else [],
            'url': job.Url or '',
        })

    return results

def search_bootcamps_by_vector(db: Session,
                                query: str,
                                limit: int = 2) -> List[Dict]:
    '''
    벡터 유사도 기반 부트캠프 검색
    
    Args:
        db: SQLAlchemy 세션
        query: 사용자 질문
        limit: 반환할 결과 수 (기본값: 2)
    
    Returns:
        List[Dict]: 부트캠프 리스트 (_format_bootcamp_card 호환 형식)
    '''
    from src.models import BootcampPost  # 순환 import 방지
    
    # 1. 쿼리를 벡터로 변환
    query_vector = get_query_embedding(query)

    # 2. cosine 유사도로 검색
    #    임계값 0.5 초과만 추천
    bootcamps = db.query(BootcampPost).filter(
        BootcampPost.Embeded.isnot(None),
        # BootcampPost.Embeded.cosine_distance(query_vector) < 0.1 # 임시로 임계값 없앰
    ).order_by(
        BootcampPost.Embeded.cosine_distance(query_vector)
    ).limit(limit).all()

    # for bc in bootcamps:
    #     logging.debug(f"[VECTOR] Result: {bc.Title} | Company: {bc.CompanyName}")
    
    # 3. _format_bootcamp_card()가 기대하는 형식으로 반환
    results = []
    for bc in bootcamps:
        # 카테고리명 안전하게 가져오기
        category_name = ''
        if bc.job_category:
            category_name = bc.job_category.CategoryName
        
        # 필요없는 old_column 수정
        results.append({
            # _format_bootcamp_card()가 직접 사용하는 키
            'name': bc.Title or '부트캠프명 없음',
            'description': (bc.EducationContent or '').replace('\n', '').replace('\r', ' ')[:40] + '...' if bc.EducationContent and len(bc.EducationContent) > 100 else (bc.EducationContent or '교육 내용 없음'),
            
            # _format_bootcamp_card()가 extra에서 가져오는 키
            'extra': {
                'institute': bc.InstituteName or '기관명 없음',
                'cost_type': bc.CostSupportType or '본인부담',
                'online_offline': bc.OnlineOffline or '온라인',
                'location': bc.Location or '온라인',
                'category': category_name,
                'link': bc.DetailUrl or '',
            }
        })
    
    logging.debug(f"[VECTOR] Found {len(results)} bootcamps")  # 디버깅용
    return results