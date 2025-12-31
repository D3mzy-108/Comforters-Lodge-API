from __future__ import annotations

from datetime import date
from typing import List, Optional

import django
django.setup()  # Ensures Django is initialized when FastAPI imports models.

from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import DailyPost, DailyDevotion
from .schemas import DailyPostOut, DailyDevotionOut
from .utils import parse_tsv_bytes
from asgiref.sync import sync_to_async



api = FastAPI(title="Comforters Lodge API")
# ----------------------------------------
# CORS
# ----------------------------------------
# Allow React dev server (Vite) to call the API during development.
# TODO: Allow live domain to call the API
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, DELETE, etc.
    allow_headers=["*"],   # Authorization, Content-Type, etc.
)



# -------------------------
# Helpers (serialization)
# -------------------------

def post_to_out(p: DailyPost) -> DailyPostOut:
    return DailyPostOut(
        id=p.id,
        opening_hook=p.opening_hook,
        personal_question=p.personal_question,
        biblical_qa=p.biblical_qa,
        reflection=p.reflection,
        story=p.story,
        prayer=p.prayer,
        activity_guide=p.activity_guide,
        date_posted=p.date_posted,
    )

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
# Endpoints: DailyPost
# -------------------------

@api.get("/posts", response_model=List[DailyPostOut])
def list_posts():
    """
    Fetch all daily posts from newest to oldest.

    Ordering is handled by the model Meta.ordering:
      -date_posted, -created_at
    """
    return [post_to_out(p) for p in DailyPost.objects.all()]


@api.get("/posts/{post_id}", response_model=DailyPostOut)
def get_post(post_id: int):
    """
    Fetch post by ID.
    """
    p = get_object_or_404(DailyPost, id=post_id)
    return post_to_out(p)


@api.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """
    Delete post by ID.
    """
    p = DailyPost.objects.filter(id=post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    p.delete()
    return {"deleted": True, "id": post_id}


@api.post("/posts", response_model=List[DailyPostOut])
async def create_post(
    # SINGLE POST FIELDS (multipart form fields)
    opening_hook: Optional[str] = Form(default=None),
    personal_question: Optional[str] = Form(default=None),
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
            rows = parse_tsv_bytes(raw)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Define a sync function that does all DB work (transaction + inserts).
        def _bulk_insert_posts():
            created: List[DailyPost] = []
            with transaction.atomic():
                for r in rows:
                    created.append(
                        DailyPost.objects.create(
                            opening_hook=r["opening_hook"].strip(),
                            personal_question=r["personal_question"].strip(),
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
        "opening_hook": opening_hook,
        "personal_question": personal_question,
        "biblical_qa": biblical_qa,
        "reflection": reflection,
        "story": story,
        "prayer": prayer,
        "activity_guide": activity_guide,
    }
    missing = [k for k, v in required.items() if v is None or str(v).strip() == ""]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required form fields: {missing}. "
                   f"Either provide all fields for a single post, or upload a TSV as tsv_file."
        )

    def _create_single_post():
        return DailyPost.objects.create(
            opening_hook=opening_hook.strip(),
            personal_question=personal_question.strip(),
            biblical_qa=biblical_qa.strip(),
            reflection=reflection.strip(),
            story=story.strip(),
            prayer=prayer.strip(),
            activity_guide=activity_guide.strip(),
            date_posted=date_posted or None,
        )

    p = await sync_to_async(_create_single_post, thread_sensitive=True)()
    return [post_to_out(p)]



# -------------------------
# Endpoints: DailyDevotion
# -------------------------

@api.get("/devotions", response_model=List[DailyDevotionOut])
def list_devotions():
    """
    Fetch all daily devotions from newest to oldest.
    """
    return [devotion_to_out(d) for d in DailyDevotion.objects.all()]


@api.get("/devotions/{devotion_id}", response_model=DailyDevotionOut)
def get_devotion(devotion_id: int):
    """
    Fetch devotional by ID.
    """
    d = get_object_or_404(DailyDevotion, id=devotion_id)
    return devotion_to_out(d)


@api.delete("/devotions/{devotion_id}")
def delete_devotion(devotion_id: int):
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


@api.post("/devotions", response_model=DailyDevotionOut)
async def create_devotion(
    # cover_image: UploadFile = File(...),
    citation: str = Form(...),
    verse_content: str = Form(...),
    date_posted: Optional[date] = Form(default=None),
):
    if not citation.strip():
        raise HTTPException(status_code=400, detail="citation cannot be empty")
    if not verse_content.strip():
        raise HTTPException(status_code=400, detail="verse_content cannot be empty")

    # img_bytes = await cover_image.read()
    # if not img_bytes:
    #     raise HTTPException(status_code=400, detail="cover_image upload is empty")

    # filename = cover_image.filename or "cover.jpg"

    def _create_devotion_with_image():
        """
        Sync-only block:
        - Create DB record
        - Save image using Django storage backend
        """
        d = DailyDevotion.objects.create(
            citation=citation.strip(),
            verse_content=verse_content.strip(),
            date_posted=date_posted or None,
        )
        # d.cover_image.save(filename, ContentFile(img_bytes), save=True)
        return d

    d = await sync_to_async(_create_devotion_with_image, thread_sensitive=True)()
    return devotion_to_out(d)
