from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.database import get_db
from src import models
from src.routers.comparison import job_to_dict, bootcamp_to_dict

router = APIRouter(prefix="/search", tags=["검색 기능"])

logger = logging.getLogger(__name__)


@router.get('/')
def search(
	keyword: Optional[str] = Query(None, description = "검색 키워드"),
	skills: Optional[List[str]] = Query(None, description = "기술 스택 필터 (배열)"),
	source: Optional[str] = Query(None, description = "항목 필터: 전체/채용/부트캠프"),
	career_level_id: Optional[int] = Query(None, description = "커리어 레벨 ID"),
	experience_range_id: Optional[int] = Query(None, description = "경력 구간 ID"),
	limit: int = Query(20, ge=1, le=100, description = "최대 반환 개수"),
	random_order: bool = Query(False, description = "랜덤 정렬 여부"),
	db: Session = Depends(get_db),
):
	"""
	키워드 및 필터로 채용공고(JobPost)와 부트캠프(BootcampPost)를 검색하여
	분리된 리스트로 반환합니다.
	
	필터:
	- keyword: 텍스트 검색 (선택적)
	- skills: 기술 스택 배열 (선택적)
	- source: 전체/채용/부트캠프 (선택적)
	- career_level_id: 커리어 레벨 ID (선택적)
	- experience_range_id: 경력 구간 ID (선택적)
	"""
	try:
		# 키워드 검색 조건
		keyword_filters = []
		if keyword:
			keyword_filters = [
				models.JobPost.Title.ilike(f"%{keyword}%"),
				models.JobPost.CompanyName.ilike(f"%{keyword}%"),
				models.JobPost.MainTasks.ilike(f"%{keyword}%"),
				models.JobPost.Qualifications.ilike(f"%{keyword}%"),
				models.JobPost.Preferences.ilike(f"%{keyword}%"),
				models.JobPost.Benefits.ilike(f"%{keyword}%"),
			]

		# 기술 스택 필터
		skill_filters = []
		if skills and len(skills) > 0:
			# Skill 테이블에서 스킬 이름으로 SkillID 찾기
			skill_ids = [s.SkillID for s in db.query(models.Skill).filter(
				models.Skill.SkillName.in_(skills)
			).all()]
			
			if skill_ids:
				# 해당 스킬을 가진 JobPost 찾기
				job_ids_with_skills = [
					jps.PostID for jps in db.query(models.JobPostSkill).filter(
						models.JobPostSkill.SkillID.in_(skill_ids)
					).all()
				]
				
				if job_ids_with_skills:
					skill_filters.append(models.JobPost.PostID.in_(job_ids_with_skills))
				else:
					# 스킬을 가진 JobPost가 없으면 빈 결과
					skill_filters.append(False)
			else:
				# 해당 스킬이 없으면 빈 결과
				skill_filters.append(False)

		# 경력 구간 필터
		experience_filters = []
		if experience_range_id:
			exp_range = db.query(models.ExperienceRange).filter(
				models.ExperienceRange.RangeID == experience_range_id
			).first()
			if exp_range:
				if exp_range.MinYears is not None and exp_range.MaxYears is not None:
					experience_filters.append(
						and_(
							models.JobPost.MinExperienceYears >= exp_range.MinYears,
							models.JobPost.MinExperienceYears <= exp_range.MaxYears
						)
					)
				elif exp_range.MinYears is not None:
					experience_filters.append(
						models.JobPost.MinExperienceYears >= exp_range.MinYears
					)
				elif exp_range.MaxYears is not None:
					experience_filters.append(
						models.JobPost.MinExperienceYears <= exp_range.MaxYears
					)

		# JobPost 쿼리 구성
		jobs_q = db.query(models.JobPost)
		
		# 필터 적용
		all_filters = []
		if keyword_filters:
			all_filters.append(or_(*keyword_filters))
		if skill_filters:
			all_filters.extend(skill_filters)
		if experience_filters:
			all_filters.extend(experience_filters)
		
		if all_filters:
			jobs_q = jobs_q.filter(and_(*all_filters))
		
		# source 필터 적용
		if source == "채용":
			# JobPost만 반환 (이미 jobs_q에 있음)
			pass
		elif source == "부트캠프":
			# JobPost는 빈 리스트로
			jobs_q = jobs_q.filter(False)
		
		# 랜덤 정렬 적용
		if random_order:
			# PostgreSQL/SQLite의 경우 func.random(), MySQL의 경우 func.rand() 사용
			# 대부분의 DB에서 func.random()을 지원하므로 사용
			jobs_q = jobs_q.order_by(func.random())

		
		jobs_q = jobs_q.limit(limit)
		jobs = [job_to_dict(j) for j in jobs_q.all()]

		# BootcampPost 쿼리 구성
		bootcamp_keyword_filters = []
		if keyword:
			bootcamp_keyword_filters = [
				models.BootcampPost.Title.ilike(f"%{keyword}%"),
				models.BootcampPost.InstituteName.ilike(f"%{keyword}%"),
				models.BootcampPost.EducationContent.ilike(f"%{keyword}%"),
				models.BootcampPost.Qualification.ilike(f"%{keyword}%"),
				models.BootcampPost.Benefits.ilike(f"%{keyword}%"),
			]

		# 부트캠프 기술 스택 필터
		bootcamp_skill_filters = []
		if skills and len(skills) > 0:
			# 각 기술스택이 부트캠프의 텍스트 필드에 포함되어 있는지 확인
			# 모든 선택된 기술스택이 포함되어야 함 (AND 조건)
			for skill in skills:
				skill_filter = or_(
					models.BootcampPost.Title.ilike(f"%{skill}%"),
					models.BootcampPost.InstituteName.ilike(f"%{skill}%"),
					models.BootcampPost.EducationContent.ilike(f"%{skill}%"),
					models.BootcampPost.Qualification.ilike(f"%{skill}%"),
					models.BootcampPost.Benefits.ilike(f"%{skill}%"),
				)
				bootcamp_skill_filters.append(skill_filter)

		bootcamps_q = db.query(models.BootcampPost)
		
		bootcamp_filters = []
		if bootcamp_keyword_filters:
			bootcamp_filters.append(or_(*bootcamp_keyword_filters))
		if bootcamp_skill_filters:
			# 모든 기술스택이 포함되어야 함 (AND 조건)
			bootcamp_filters.extend(bootcamp_skill_filters)
		
		if bootcamp_filters:
			bootcamps_q = bootcamps_q.filter(and_(*bootcamp_filters))
		
		# source 필터 적용
		if source == "부트캠프":
			# BootcampPost만 반환 (이미 bootcamps_q에 있음)
			pass
		elif source == "채용":
			# BootcampPost는 빈 리스트로
			bootcamps_q = bootcamps_q.filter(False)
		
		# 랜덤 정렬 적용
		if random_order:
			# PostgreSQL/SQLite의 경우 func.random(), MySQL의 경우 func.rand() 사용
			bootcamps_q = bootcamps_q.order_by(func.random())
		
		bootcamps_q = bootcamps_q.limit(limit)
		bootcamps = [bootcamp_to_dict(b) for b in bootcamps_q.all()]

		return {"jobs": jobs, "bootcamps": bootcamps}
	except Exception as e:
		logger.exception("Search failed: %s", e)
		raise HTTPException(status_code=500, detail="Internal Server Error")