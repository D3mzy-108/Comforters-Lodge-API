from __future__ import annotations
from fastapi import File, Form, HTTPException, UploadFile
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from datetime import date
from typing import List, Optional, Dict, Any

import django

from lodge.api_features.devotionals import (
    _create_devotion, _daily_devotions, _delete_devotion, _edit_devotion, _get_devotion, _list_devotions)
from lodge.api_features.hymns import _create_hymn, _delete_hymn, _edit_hymn, _get_hymn, _grouped_hymn_list, _hymns_list
from lodge.api_features.lessons import (
    _create_post, _daily_lesson_list, _delete_post, _edit_post, _get_post, _list_posts)
from lodge.schemas import DailyPostOut, DailyDevotionOut, GroupedHymnOut, HymnOut
django.setup()


api = FastAPI(title="Comforters Lodge API")
# ----------------------------------------
# CORS
# ----------------------------------------
# Allow React dev server (Vite) to call the API during development.
# Allows live domain to call the API
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://cm.clm.org.ng",
        "https://www.cm.clm.org.ng",
        "https://clm.org.ng",
        "https://www.clm.org.ng",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, DELETE, etc.
    allow_headers=["*"],   # Authorization, Content-Type, etc.
)


# -----------------------------
# LESSON ENDPOINTS
# -----------------------------
@api.get("/posts")
def list_posts(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    return _list_posts(page)


@api.get("/posts/daily-lessons")
def daily_lesson_list(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    return _daily_lesson_list(page)


@api.get("/posts/{post_id}", response_model=DailyPostOut)
def get_post(post_id: int):
    return _get_post(post_id)


@api.delete("/posts/{post_id}")
def delete_post(post_id: int):
    return _delete_post(post_id)


@api.post("/posts", response_model=List[DailyPostOut])
async def create_post(
    # SINGLE POST FIELDS (multipart form fields)
    series_title: Optional[str] = Form(default=None),
    personal_question: Optional[str] = Form(default=None),
    theme: Optional[str] = Form(default=None),
    opening_hook: Optional[str] = Form(default=None),
    biblical_qa: Optional[str] = Form(default=None),
    reflection: Optional[str] = Form(default=None),
    story: Optional[str] = Form(default=None),
    prayer: Optional[str] = Form(default=None),
    activity_guide: Optional[str] = Form(default=None),
    date_posted: Optional[date] = Form(default=None),

    # BULK TSV UPLOAD (also multipart)
    tsv_file: Optional[UploadFile] = File(default=None),
):
    return await _create_post(
        series_title=series_title,
        personal_question=personal_question,
        theme=theme, opening_hook=opening_hook,
        biblical_qa=biblical_qa,
        reflection=reflection,
        story=story,
        prayer=prayer,
        activity_guide=activity_guide,
        date_posted=date_posted,
        tsv_file=tsv_file
    )


@api.patch("/posts/{post_id}", response_model=List[DailyPostOut])
def edit_post(
    post_id: int,
    # SINGLE POST FIELDS (multipart form fields)
    series_title: Optional[str] = Form(default=None),
    personal_question: Optional[str] = Form(default=None),
    theme: Optional[str] = Form(default=None),
    opening_hook: Optional[str] = Form(default=None),
    biblical_qa: Optional[str] = Form(default=None),
    reflection: Optional[str] = Form(default=None),
    story: Optional[str] = Form(default=None),
    prayer: Optional[str] = Form(default=None),
    activity_guide: Optional[str] = Form(default=None),
):
    update_data = {
        "series_title": series_title,
        "personal_question": personal_question,
        "theme": theme,
        "opening_hook": opening_hook,
        "biblical_qa": biblical_qa,
        "reflection": reflection,
        "story": story,
        "prayer": prayer,
        "activity_guide": activity_guide,
    }

    # keep only fields actually provided (None means “don’t change”)
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided to update.")
    return _edit_post(
        post_id=post_id,
        **update_data
    )


# -----------------------------
# DEVOTIONAL ENDPOINTS
# -----------------------------
@api.get("/devotions")
def list_devotions(page: int = Query(1, ge=1)):
    return _list_devotions(page)


@api.get("/daily-devotions")
def daily_devotions(page: int = Query(1, ge=1)):
    return _daily_devotions(page)


@api.get("/devotions/{devotion_id}", response_model=DailyDevotionOut)
def get_devotion(devotion_id: int):
    return _get_devotion(devotion_id)


@api.delete("/devotions/{devotion_id}")
def delete_devotion(devotion_id: int):
    return _delete_devotion(devotion_id)


@api.post("/devotions", response_model=List[DailyDevotionOut])
async def create_devotion(
    # SINGLE DEVOTION FIELDS (multipart form fields)
    citation: Optional[str] = Form(default=None),
    verse_content: Optional[str] = Form(default=None),
    date_posted: Optional[date] = Form(default=None),

    # BULK TSV UPLOAD (also multipart)
    tsv_file: Optional[UploadFile] = File(default=None),
):
    return await _create_devotion(
        citation=citation,
        verse_content=verse_content,
        date_posted=date_posted,
        tsv_file=tsv_file,
    )


@api.patch("/devotions/{devotion_id}", response_model=List[DailyDevotionOut])
def edit_devotion(
    devotion_id: int,
    # SINGLE DEVOTION FIELDS (multipart form fields)
    citation: Optional[str] = Form(default=None),
    verse_content: Optional[str] = Form(default=None),
):
    update_data = {
        "citation": citation,
        "verse_content": verse_content,
    }

    # keep only fields actually provided (None means “don’t change”)
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided to update.")

    return _edit_devotion(
        devotion_id=devotion_id,
        **update_data,
    )

# -----------------------------
# HYMN ENDPOINTS
# -----------------------------


@api.get("/hymns", response_model=Dict[str, Any])
def hymns_list(page: int = Query(1, ge=1)) -> Dict[str, Any]:
    return _hymns_list(page)


@api.get("/hymns/grouped", response_model=List[GroupedHymnOut])
def grouped_hymn_list() -> List[GroupedHymnOut]:
    return _grouped_hymn_list()


@api.get("/hymns/{hymn_id}", response_model=HymnOut)
def get_hymn(hymn_id: int) -> HymnOut:
    return _get_hymn(hymn_id)


@api.delete("/hymns/{hymn_id}", response_model=Dict[str, Any])
def delete_hymn(hymn_id: int) -> Dict[str, Any]:
    return _delete_hymn(hymn_id)


@api.post("/hymns", response_model=List[HymnOut])
async def create_hymn(
    # SINGLE HYMN FIELDS
    hymn_number: Optional[int] = Form(default=None),
    hymn_title: Optional[str] = Form(default=None),
    classification: Optional[str] = Form(default=None),
    tune_ref: Optional[str] = Form(default=None),
    cross_ref: Optional[str] = Form(default=None),
    scripture: Optional[str] = Form(default=None),
    chorus_title: Optional[str] = Form(default=None),
    chorus: Optional[str] = Form(default=None),
    verses: Optional[List[str]] = Form(default=None),

    # BULK TSV UPLOAD
    tsv_file: Optional[UploadFile] = File(default=None),
) -> List[HymnOut]:
    return await _create_hymn(
        hymn_number=hymn_number,
        hymn_title=hymn_title,
        classification=classification,
        tune_ref=tune_ref,
        cross_ref=cross_ref,
        scripture=scripture,
        chorus_title=chorus_title,
        chorus=chorus,
        verses=verses,
        tsv_file=tsv_file,
    )


@api.patch("/hymns/{hymn_id}", response_model=List[HymnOut])
def edit_hymn(
    hymn_id: int,

    # Hymn Data
    hymn_number: Optional[int] = Form(default=None),
    hymn_title: Optional[str] = Form(default=None),
    classification: Optional[str] = Form(default=None),
    tune_ref: Optional[str] = Form(default=None),
    cross_ref: Optional[str] = Form(default=None),
    scripture: Optional[str] = Form(default=None),
    chorus_title: Optional[str] = Form(default=None),
    chorus: Optional[str] = Form(default=None),
    verses: Optional[List[str]] = Form(default=None),
):
    update_data = {
        "hymn_number": hymn_number,
        "hymn_title": hymn_title,
        "classification": classification,
        "tune_ref": tune_ref,
        "cross_ref": cross_ref,
        "scripture": scripture,
        "chorus_title": chorus_title,
        "chorus": chorus,
        "verses": verses,
    }

    # keep only fields actually provided (None means “don’t change”)
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided to update.")

    return _edit_hymn(hymn_id=hymn_id, **update_data)
