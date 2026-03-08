from django.shortcuts import get_object_or_404
from lodge.models import Prayer, PrayerCategory
from lodge.schemas import PrayerCategoryCreate, PrayerCategoryUpdate, PrayerCreate, PrayerUpdate


# --- Category CRUD ---

def _get_category(category_id: int):
    return get_object_or_404(PrayerCategory, id=category_id)


def _get_categories(skip: int = 0, limit: int = 100):
    return PrayerCategory.objects.all().order_by('title')[skip: skip + limit]


def _create_category(category: PrayerCategoryCreate):
    db_category = PrayerCategory(**category.model_dump())
    db_category.save()
    return db_category


def _update_category(category_id: int, category: PrayerCategoryUpdate):
    db_category = _get_category(category_id)
    if db_category:
        update_data = category.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)
        db_category.save()
    return db_category


def _delete_category(category_id: int):
    db_category = _get_category(category_id)
    if db_category:
        db_category.delete()
    return db_category


# --- Prayer CRUD ---

def _get_prayer(prayer_id: int):
    return get_object_or_404(Prayer, id=prayer_id)


def _get_prayers(type_id: int, skip: int = 0, limit: int = 100):
    # Sorting by category title and then sub_type, similar to Django's Meta ordering
    return Prayer.objects.select_related('type').filter(type__id=type_id).order_by('type__title', 'sub_type')[skip: skip + limit]


def _create_prayer(prayer: PrayerCreate):
    db_prayer = Prayer(**prayer.model_dump())
    db_prayer.save()
    return db_prayer


def _update_prayer(prayer_id: int, prayer: PrayerUpdate):
    db_prayer = _get_prayer(prayer_id)
    if db_prayer:
        update_data = prayer.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_prayer, key, value)
        db_prayer.save()
    return db_prayer


def _delete_prayer(prayer_id: int):
    db_prayer = _get_prayer(prayer_id)
    if db_prayer:
        db_prayer.delete()
    return db_prayer
