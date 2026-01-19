from __future__ import annotations

from datetime import date
from typing import List, Optional
from math import ceil

import django
from django.utils import timezone

from django.db import transaction
# from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from fastapi import File, Form, HTTPException, UploadFile

from ..models import DailyDevotion
from ..schemas import DailyDevotionOut
from ..utils import parse_tsv_bytes
from asgiref.sync import sync_to_async


# -------------------------
# Helpers (serialization)
# -------------------------

def devotion_to_out(d: DailyDevotion) -> DailyDevotionOut:
    # cover_image.url works when MEDIA_URL/MEDIA_ROOT are configured;
    # in production you'll typically serve media via nginx/s3/etc.
    # url = d.cover_image.url if d.cover_image else ""
    return DailyDevotionOut(
        id=d.id,
        # cover_image_url=url,
        citation=d.citation,
        verse_content=d.verse_content,
        date_posted=d.date_posted,
    )


# -------------------------
# Endpoints: DailyDevotion
# -------------------------

def _list_devotions(page: int):
    """
    Fetch all daily devotions from newest to oldest.
    """
    page_size = 10

    qs = DailyDevotion.objects.all().order_by('-date_posted')
    total_count = qs.count()

    # If there are no posts, keep total_pages at 0 and return an empty list.
    total_pages = ceil(total_count / page_size) if total_count > 0 else 0

    # If client requests a page beyond total_pages, return empty posts (or raise 404 if you prefer).
    offset = (page - 1) * page_size
    page_items = qs[offset: offset + page_size]

    return {
        "devotionals": [devotion_to_out(p) for p in page_items],
        "page": page,
        "total_pages": total_pages,
    }


def _daily_devotions(page: int):
    """
    Fetch devotions for each day starting today
    """
    page_size = 12
    today = timezone.localdate()
    devotions = (
        DailyDevotion.objects
        .filter(date_posted__lte=today)
        .order_by("-date_posted", "-id")
    )

    offset = (page - 1) * page_size
    page_items = devotions[offset: offset + page_size]

    return {
        "devotionals": [devotion_to_out(p) for p in page_items],
        "page": page,
    }


def _get_devotion(devotion_id: int):
    """
    Fetch devotional by ID.
    """
    d = get_object_or_404(DailyDevotion, id=devotion_id)
    return devotion_to_out(d)


def _delete_devotion(devotion_id: int):
    """
    Delete devotional by ID.
    """
    d = DailyDevotion.objects.filter(id=devotion_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devotional not found")

    # Optional cleanup: remove file from storage when deleting record.
    # This prevents orphaned files in MEDIA_ROOT.
    if d.cover_image and default_storage.exists(d.cover_image.name):
        default_storage.delete(d.cover_image.name)

    d.delete()
    return {"deleted": True, "id": devotion_id}


async def _create_devotion(
    # SINGLE DEVOTION FIELDS (multipart form fields)
    citation: Optional[str] = Form(default=None),
    verse_content: Optional[str] = Form(default=None),
    date_posted: Optional[date] = Form(default=None),

    # BULK TSV UPLOAD (also multipart)
    tsv_file: Optional[UploadFile] = File(default=None),
):
    """
    IMPORTANT:
    - This endpoint is async (FastAPI).
    - Django ORM is sync-only.
    - Therefore, all ORM work must run in a thread using sync_to_async.

    Modes:
    1) Single create: provide required form fields.
    2) Bulk upload: provide tsv_file (TSV headers: citation, verse_content, date_posted).
    """

    # --------------------------
    # Mode 2: TSV bulk upload
    # --------------------------
    if tsv_file is not None:
        raw = await tsv_file.read()
        if not raw:
            raise HTTPException(
                status_code=400, detail="tsv_file upload is empty")

        try:
            # returns List[Dict[str, Any]]
            rows = parse_tsv_bytes(raw, "DEVOTIONAL")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _bulk_insert_devotions():
            created: List[DailyDevotion] = []
            with transaction.atomic():
                for r in rows:
                    created.append(
                        DailyDevotion.objects.create(
                            citation=r["citation"].strip(),
                            verse_content=r["verse_content"].strip(),
                            # already parsed to date
                            date_posted=r["date_posted"],
                        )
                    )
            return created

        created = await sync_to_async(_bulk_insert_devotions, thread_sensitive=True)()
        return [devotion_to_out(d) for d in created]

    # --------------------------
    # Mode 1: Single create
    # --------------------------
    required = {
        "citation": citation,
        "verse_content": verse_content,
    }
    missing = [k for k, v in required.items(
    ) if v is None or str(v).strip() == ""]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing required form fields: {missing}. "
                f"Either provide all fields for a single devotion, or upload a TSV as tsv_file."
            ),
        )

    def _create_single_devotion():
        return DailyDevotion.objects.create(
            citation=citation.strip(),
            verse_content=verse_content.strip(),
            date_posted=date_posted or timezone.localdate(),
        )

    d = await sync_to_async(_create_single_devotion, thread_sensitive=True)()
    return [devotion_to_out(d)]


def _edit_devotion(
    devotion_id: int,
    **update_data,
):
    d = DailyDevotion.objects.filter(id=devotion_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devotional not found")

    for field, value in update_data.items():
        setattr(d, field, value)
    d.save()
    return [devotion_to_out(d)]
