from __future__ import annotations

from typing import List, Optional

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from fastapi import HTTPException

from ..models import Hymnal
from ..schemas import HymnalCreate, HymnalResponse, HymnalUpdate


def hymnal_to_out(h: Hymnal) -> HymnalResponse:
    return HymnalResponse(id=h.id, name=h.name, color_code=h.color_code)


def _get_hymnals(skip: int = 0, limit: int = 100) -> List[HymnalResponse]:
    hymnals = Hymnal.objects.all()[skip: skip + limit]
    return [hymnal_to_out(h) for h in hymnals]


def _get_hymnal(hymnal_id: int) -> Optional[HymnalResponse]:
    hymnal = Hymnal.objects.filter(id=hymnal_id).first()
    return hymnal_to_out(hymnal) if hymnal else None


def _create_hymnal(hymnal: HymnalCreate) -> HymnalResponse:
    if not hymnal.name or not hymnal.name.strip():
        raise HTTPException(status_code=400, detail="Hymnal name is required.")
    created = Hymnal.objects.create(
        name=hymnal.name.strip(),
        color_code=(hymnal.color_code or "").strip(),
    )
    return hymnal_to_out(created)


def _update_hymnal(hymnal_id: int, hymnal: HymnalUpdate) -> Optional[HymnalResponse]:
    db_hymnal = Hymnal.objects.filter(id=hymnal_id).first()
    if not db_hymnal:
        return None
    if hymnal.name is not None:
        db_hymnal.name = hymnal.name.strip()
    if hymnal.color_code is not None:
        db_hymnal.color_code = hymnal.color_code.strip()
    db_hymnal.save()
    return hymnal_to_out(db_hymnal)


def _delete_hymnal(hymnal_id: int) -> Optional[dict]:
    hymnal = Hymnal.objects.filter(id=hymnal_id).first()
    if not hymnal:
        return None
    try:
        hymnal.delete()
    except ProtectedError:
        raise HTTPException(
            status_code=400,
            detail="This hymnal still has hymns. Move or delete them first.",
        )
    return {"deleted": True, "id": hymnal_id}


def resolve_hymnal(hymnal_id: Optional[int]) -> Hymnal:
    """Return the requested hymnal, or fall back to the first one.

    Used by hymn create so callers that don't yet send a hymnal (e.g. the
    current admin) still land in a valid book instead of erroring.
    """
    if hymnal_id is not None:
        return get_object_or_404(Hymnal, pk=hymnal_id)
    fallback = Hymnal.objects.order_by("id").first()
    if fallback is None:
        raise HTTPException(
            status_code=400,
            detail="No hymnal exists yet. Create a hymnal before adding hymns.",
        )
    return fallback
