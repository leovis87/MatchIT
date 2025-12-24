from sqlalchemy import desc, asc, nulls_last
from src import models


def get_order_clause(model_class, sort: str):
    """
    주어진 모델 클래스와 정렬 옵션에 따라 SQLAlchemy order_by 절을 반환합니다.

    Args:
        model_class: JobPost 또는 BootcampPost 모델 클래스
        sort: 정렬 옵션 ('created', 'views', 'deadline')

    Returns:
        SQLAlchemy order_by 절
    """
    if sort == "created":
        return model_class.CreatedAt.desc()
    elif sort == "views":
        return model_class.ViewCount.desc()
    elif sort == "deadline":
        # deadline은 CloseDate 오름차순 (마감일 가까운 순)
        return model_class.CloseDate.asc().nulls_last()
    else:
        # 기본값: 최신순
        return model_class.CreatedAt.desc()