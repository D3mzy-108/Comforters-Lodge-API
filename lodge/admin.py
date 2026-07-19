from django.contrib import admin
from .models import DailyPost, DailyDevotion, Hymn, Hymnal, Prayer


@admin.register(Hymnal)
class HymnalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color_code", "created_at")
    search_fields = ("name",)


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
    list_display = ("id", "hymnal", "hymn_number", "hymn_title",
                    "classification", "created_at")
    list_filter = ("hymnal",)
    search_fields = ("hymn_title", "classification", "tune_ref", "scripture")


@admin.register(Prayer)
class PrayerAdmin(admin.ModelAdmin):
    list_display = ('type__title', 'sub_type', 'prayer')
    list_filter = ('type', 'sub_type')
    readonly_fields = ('type', 'sub_type', 'prayer')
    search_fields = ('type__title', 'sub_type', 'prayer')
