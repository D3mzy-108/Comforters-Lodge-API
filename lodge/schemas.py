from datetime import date
from pydantic import BaseModel


class DailyPostOut(BaseModel):
    id: int
    series_title: str
    personal_question: str
    theme: str
    opening_hook: str
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


class HymnOut(BaseModel):
    id: int
    hymn_number: int
    hymn_title: str
    classification: str
    tune_ref: str
    cross_ref: str
    scripture: str
    chorus_title: str
    chorus: str
    verses: list[str]
