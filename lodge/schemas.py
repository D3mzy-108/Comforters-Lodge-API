from datetime import date, datetime
from typing import Optional
from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field


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
    prayer: str
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


class GroupedHymnOut(BaseModel):
    group: str
    hymns: list[HymnOut]


class PrayerCategoryBase(BaseModel):
    title: str = Field(..., max_length=255,
                       description="Title of the prayer type")
    subtitle: str = Field(..., max_length=255,
                          description="Subtitle or description")
    color_code: str = Field(..., max_length=255,
                            description="Color code for the prayer type")


class PrayerCategoryCreate(PrayerCategoryBase):
    title: Optional[str] = Form(default=None)
    subtitle: Optional[str] = Form(default=None)
    color_code: Optional[str] = Form(default=None)


class PrayerCategoryUpdate(PrayerCategoryBase):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    color_code: Optional[str] = None


class PrayerCategoryResponse(PrayerCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PrayerBase(BaseModel):
    sub_type: str
    prayer: str
    type_id: int


class PrayerCreate(PrayerBase):
    sub_type: Optional[str] = Form(default=None)
    prayer: Optional[str] = Form(default=None)
    type_id: Optional[int] = Form(default=0)


class PrayerUpdate(BaseModel):
    sub_type: Optional[str] = None
    prayer: Optional[str] = None
    type_id: Optional[int] = None


class PrayerResponse(PrayerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
