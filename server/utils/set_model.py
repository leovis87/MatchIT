"""
구성

1. Model의 prompt 설정 함수
2. 
    - 
"""
from typing import List, Dict, Tuple, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.DEBUG,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'set_model_logging.log'
)

# ========================================================================
# 🔥 코드로 확실하게 포맷팅하는 함수들
# ========================================================================
def _format_job_card(self, job: Dict, index: int, gap: Dict = None) -> str:
    """채용공고 카드 포맷팅 - 코드로 확실하게!"""
    skills_str = ', '.join(job['skills'][:4]) if job['skills'] else '스킬 미기재'
    
    company_display = job['company']
    if job.get('url'):
        company_display = f"[{job['company']}]({job['url']})"
    
    card = f"""
🏢 **{company_display}**
📌 {job['title']}
📍 {job['location']} | 💼 {job['experience']} | 💰 {job['salary']}
🛠️ {skills_str}"""

    return card

def _format_bootcamp_card(self,
                            card: Dict) -> str:
    """부트캠프 추천 카드 포맷팅"""
    cost_emoji = "🆓" if "국비" in card['extra'].get('cost_type', '') else "💳"

    # 이름을 Markdown 링크로 변환
    # URL이 있으면 Markdown 링크
    name_display = card.get('name', '부트캠프명 없음')
    if card['extra'].get('link'):
        name_display = f"[{name_display}]({card['extra']['link']})"

    formatted = f"""
🎓 {name_display}
📍 {card['extra'].get('institute', '기관 미기재')} | {cost_emoji} {card['extra'].get('cost_type', '')} | {card['extra'].get('online_offline', '')}
📍 {card['extra'].get('location', '온라인')}
💡 {card.get('description', '')}
"""
    return formatted