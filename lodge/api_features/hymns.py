from __future__ import annotations

from ..utils import parse_tsv_bytes
from ..schemas import HymnOut
from ..models import Hymn

from fastapi import File, Form, HTTPException, UploadFile, Query
from django.shortcuts import get_object_or_404
from django.db import transaction
from asgiref.sync import sync_to_async

from typing import List, Optional, Dict, Any


# -------------------------
# Helpers (serialization)
# -------------------------

def hymn_to_out(h: Hymn) -> HymnOut:
    """Convert a Hymn model instance to HymnOut."""
    return HymnOut(
        id=h.id,
        hymn_number=h.hymn_number,
        hymn_title=h.hymn_title,
        classification=h.classification,
        tune_ref=h.tune_ref,
        cross_ref=h.cross_ref,
        scripture=h.scripture,
        chorus_title=h.chorus_title,
        chorus=h.chorus,
        verses=h.verses,
    )


# -------------------------
# Endpoints: Hymns (SYNC)
# -------------------------

def _hymns_list(page: int) -> Dict[str, Any]:
    """
    Paginated hymn list (30 per page).
    """
    PAGE_SIZE = 30
    offset = (page - 1) * PAGE_SIZE

    total = Hymn.objects.count()
    hymns = Hymn.objects.order_by("hymn_number")[offset: offset + PAGE_SIZE]

    return {
        "hymns": [hymn_to_out(h) for h in hymns],
        "page": page,
        "totalHymns": total,
    }


def _grouped_hymn_list() -> List[List[HymnOut]]:
    """
    Returns all hymns grouped into chunks of 100 (for accordion UI).
    """
    CHUNK_SIZE = 100
    hymns = list(Hymn.objects.order_by("hymn_number"))

    grouped: List[List[HymnOut]] = []
    for i in range(0, len(hymns), CHUNK_SIZE):
        grouped.append([hymn_to_out(h) for h in hymns[i:i + CHUNK_SIZE]])

    return grouped


def _get_hymn(hymn_id: int) -> HymnOut:
    """
    Fetch a single hymn by ID.
    """
    hymn = get_object_or_404(Hymn, pk=hymn_id)
    return hymn_to_out(hymn)


def _delete_hymn(hymn_id: int) -> Dict[str, Any]:
    """
    Delete a hymn by ID.
    """
    hymn = get_object_or_404(Hymn, pk=hymn_id)
    hymn.delete()
    return {"deleted": True, "id": hymn_id}


# -------------------------
# Endpoint: Create Hymns (ASYNC)
# -------------------------

async def _create_hymn(
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
    """
    Create hymns.

    Modes:
    - TSV bulk upload (preferred)
    - Single hymn creation via form fields
    """

    # --------------------------
    # Mode 1: TSV bulk upload
    # --------------------------
    if tsv_file is not None:
        raw = await tsv_file.read()
        if not raw:
            raise HTTPException(
                status_code=400, detail="tsv_file upload is empty")

        try:
            items = parse_tsv_bytes(raw, "HYMN")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _bulk_create() -> List[Hymn]:
            created: List[Hymn] = []
            with transaction.atomic():
                for item in items:
                    hymn_data = item["hymn"]
                    verses_list = item["verses"]

                    created.append(
                        Hymn.objects.create(
                            hymn_number=int(hymn_data["hymn_number"]),
                            hymn_title=hymn_data["hymn_title"].strip(),
                            classification=hymn_data["classification"].strip(),
                            tune_ref=hymn_data["tune_ref"].strip(),
                            cross_ref=hymn_data.get("cross_ref", "").strip(),
                            scripture=hymn_data.get("scripture", "").strip(),
                            chorus_title=hymn_data.get(
                                "chorus_title", "").strip(),
                            chorus=hymn_data.get("chorus", "").strip(),
                            verses=[v.strip()
                                    for v in verses_list if v.strip()],
                        )
                    )
            return created

        created = await sync_to_async(_bulk_create, thread_sensitive=True)()
        return [hymn_to_out(h) for h in created]

    # --------------------------
    # Mode 2: Single create
    # --------------------------
    required = {
        "hymn_number": hymn_number,
        "hymn_title": hymn_title,
        "classification": classification,
        "tune_ref": tune_ref,
        "verses": verses,
    }
    missing = [
        k for k, v in required.items()
        if v is None or (isinstance(v, str) and not v.strip()) or (k == "verses" and not v)
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required form fields: {missing}",
        )

    def _create_single() -> Hymn:
        return Hymn.objects.create(
            hymn_number=int(hymn_number),
            hymn_title=hymn_title.strip(),
            classification=classification.strip(),
            tune_ref=tune_ref.strip(),
            cross_ref=(cross_ref or "").strip(),
            scripture=(scripture or "").strip(),
            chorus_title=(chorus_title or "").strip(),
            chorus=(chorus or "").strip(),
            verses=[v.strip() for v in verses if v.strip()],
        )

    hymn = await sync_to_async(_create_single, thread_sensitive=True)()
    return [hymn_to_out(hymn)]
