from django.contrib import admin
from .models import DailyPost, DailyDevotion

@admin.register(DailyPost)
class DailyPostAdmin(admin.ModelAdmin):
    list_display = ("id", "date_posted", "opening_hook", "created_at")
    search_fields = ("opening_hook", "personal_question", "biblical_qa")

@admin.register(DailyDevotion)
class DailyDevotionAdmin(admin.ModelAdmin):
    list_display = ("id", "date_posted", "citation", "created_at")
    search_fields = ("citation", "verse_content")
