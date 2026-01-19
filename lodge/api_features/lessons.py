from __future__ import annotations

from datetime import date
from typing import List, Optional, Dict, Any
from math import ceil

import django
from django.utils import timezone

from django.db import transaction
# from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from fastapi import File, Form, HTTPException, UploadFile

from ..models import DailyPost
from ..schemas import DailyPostOut
from ..utils import parse_tsv_bytes
from asgiref.sync import sync_to_async

# -------------------------
# Helpers (serialization)
# -------------------------


def post_to_out(p: DailyPost) -> DailyPostOut:
    return DailyPostOut(
        id=p.id,
        series_title=p.series_title,
        personal_question=p.personal_question,
        theme=p.theme,
        opening_hook=p.opening_hook,
        biblical_qa=p.biblical_qa,
        reflection=p.reflection,
        story=p.story,
        prayer=p.prayer,
        activity_guide=p.activity_guide,
        date_posted=p.date_posted,
    )


# -------------------------
# Endpoints: DailyPost
# -------------------------

def _list_posts(page: int) -> Dict[str, Any]:
    page_size = 10

    qs = DailyPost.objects.all().order_by('-date_posted')
    total_count = qs.count()

    # If there are no posts, keep total_pages at 0 and return an empty list.
    total_pages = ceil(total_count / page_size) if total_count > 0 else 0

    # If client requests a page beyond total_pages, return empty posts (or raise 404 if you prefer).
    offset = (page - 1) * page_size
    page_items = qs[offset: offset + page_size]

    return {
        "posts": [post_to_out(p) for p in page_items],
        "page": page,
        "total_pages": total_pages,
    }


def _daily_lesson_list(page: int) -> Dict[str, Any]:
    page_size = 12
    today = timezone.localdate()  # safer than timezone.now().date()

    # Most recent 7 posts from today backwards
    posts_qs = (
        DailyPost.objects
        .filter(date_posted__lte=today)
        .order_by("-date_posted", "-id")
    )

    offset = (page - 1) * page_size
    page_items = posts_qs[offset: offset + page_size]

    # Next scheduled post after today
    up_next_obj = (
        DailyPost.objects
        .filter(date_posted__gt=today)
        .order_by("date_posted", "id")
        .first()
    )

    return {
        "posts": [post_to_out(p) for p in page_items],
        "page": page,
        "up_next": post_to_out(up_next_obj) if up_next_obj else None,
    }


def _get_post(post_id: int):
    """
    Fetch post by ID.
    """
    p = get_object_or_404(DailyPost, id=post_id)
    return post_to_out(p)


def _delete_post(post_id: int):
    """
    Delete post by ID.
    """
    p = DailyPost.objects.filter(id=post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    p.delete()
    return {"deleted": True, "id": post_id}


async def _create_post(
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
    """
    IMPORTANT:
    - This endpoint is async (FastAPI).
    - Django ORM is sync-only.
    - Therefore, all ORM work must run in a thread using sync_to_async.
    """

    # --------------------------
    # Mode 2: TSV bulk upload
    # --------------------------
    if tsv_file is not None:
        raw = await tsv_file.read()

        try:
            rows = parse_tsv_bytes(raw, 'LESSON')
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Define a sync function that does all DB work (transaction + inserts).
        def _bulk_insert_posts():
            created: List[DailyPost] = []
            with transaction.atomic():
                for r in rows:
                    created.append(
                        DailyPost.objects.create(
                            series_title=r["series_title"].strip(),
                            personal_question=r["personal_question"].strip(),
                            theme=r['theme'].strip(),
                            opening_hook=r["opening_hook"].strip(),
                            biblical_qa=r["biblical_qa"].strip(),
                            reflection=r["reflection"].strip(),
                            story=r["story"].strip(),
                            prayer=r["prayer"].strip(),
                            activity_guide=r["activity_guide"].strip(),
                            date_posted=r["date_posted"],
                        )
                    )
            return created

        created = await sync_to_async(_bulk_insert_posts, thread_sensitive=True)()
        return [post_to_out(p) for p in created]

    # --------------------------
    # Mode 1: Single create
    # --------------------------
    required = {
        'series_title': series_title,
        'personal_question': personal_question,
        'theme': theme,
        'opening_hook': opening_hook,
        'biblical_qa': biblical_qa,
        'reflection': reflection,
        'story': story,
        'prayer': prayer,
        'activity_guide': activity_guide,
    }
    missing = [k for k, v in required.items(
    ) if v is None or str(v).strip() == ""]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required form fields: {missing}. "
                   f"Either provide all fields for a single post, or upload a TSV as tsv_file."
        )

    def _create_single_post():
        return DailyPost.objects.create(
            series_title=series_title.strip(),
            personal_question=personal_question.strip(),
            theme=theme.strip(),
            opening_hook=opening_hook.strip(),
            biblical_qa=biblical_qa.strip(),
            reflection=reflection.strip(),
            story=story.strip(),
            prayer=prayer.strip(),
            activity_guide=activity_guide.strip(),
            date_posted=date_posted or timezone.localdate(),
        )

    p = await sync_to_async(_create_single_post, thread_sensitive=True)()
    return [post_to_out(p)]


def _edit_post(
    post_id: int,
    # SINGLE POST FIELDS (multipart form fields)
    **update_data
):
    p = DailyPost.objects.filter(id=post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    for field, value in update_data.items():
        setattr(p, field, value)
    p.save()
    return [post_to_out(p)]
