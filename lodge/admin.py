from django.contrib import admin
from .models import DailyPost, DailyDevotion, Hymn


@admin.register(DailyPost)
class DailyPostAdmin(admin.ModelAdmin):
    list_display = ("id", "date_posted", "opening_hook", "created_at")
    search_fields = ("opening_hook", "personal_question", "biblical_qa")


@admin.register(DailyDevotion)
class DailyDevotionAdmin(admin.ModelAdmin):
    list_display = ("id", "date_posted", "citation", "created_at")
    search_fields = ("citation", "verse_content")


@admin.register(Hymn)
class HymnAdmin(admin.ModelAdmin):
    list_display = ("id", "hymn_number", "hymn_title",
                    "classification", "created_at")
    search_fields = ("hymn_title", "classification", "tune_ref", "scripture")
