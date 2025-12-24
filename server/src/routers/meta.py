from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import json

from src.database import get_db
from src import models

router = APIRouter(prefix="", tags=["meta"])

logger = logging.getLogger(__name__)


@router.get("/careerlevels", summary = "Get career levels")
def get_career_levels(db: Session = Depends(get_db)):
    try:
        items = db.query(models.CareerLevel).order_by(models.CareerLevel.CareerLevelID).all()
        results = []
        for c in items:
            # Normalize field names for frontend
            results.append({
                "id": c.CareerLevelID,
                "name": c.CareerName,
            })
        return JSONResponse(content={"careerlevels": results}, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.exception("get_career_levels failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/experienceranges", summary="Get experience ranges")
def get_experience_ranges(db: Session = Depends(get_db)):
    try:
        items = db.query(models.ExperienceRange).order_by(models.ExperienceRange.RangeID).all()
        results = []
        for r in items:
            results.append({
                "id": r.RangeID,
                "name": r.RangeName,
                "min_years": r.MinYears,
                "max_years": r.MaxYears,
            })
        return JSONResponse(content={"experienceranges": results}, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.exception("get_experience_ranges failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/stats", summary="Get platform statistics")
def get_stats(db: Session = Depends(get_db)):
    try:
        job_count = db.query(models.JobPost).count()
        bootcamp_count = db.query(models.BootcampPost).count()
        return JSONResponse(content={
            "job_posts": job_count,
            "bootcamps": bootcamp_count
        }, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.exception("get_stats failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/desiredjobs", summary="Get desired jobs")
def get_desired_jobs(db: Session = Depends(get_db)):
    try:
        items = db.query(models.DesiredJob).order_by(models.DesiredJob.DesiredJobID).all()
        results = []
        for d in items:
            results.append({
                "id": d.DesiredJobID,
                "name": d.JobName,
            })
        return JSONResponse(content={"desiredjobs": results}, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.exception("get_desired_jobs failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
