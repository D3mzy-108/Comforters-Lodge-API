from datetime import date
from pydantic import BaseModel

class DailyPostOut(BaseModel):
    id: int
    opening_hook: str
    personal_question: str
    biblical_qa: str
    reflection: str
    story: str
    prayer: str
    activity_guide: str
    date_posted: date

class DailyDevotionOut(BaseModel):
    id: int
    # cover_image_url: str
    citation: str
    verse_content: str
    date_posted: date
