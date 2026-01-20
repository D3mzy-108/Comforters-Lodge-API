from django.db import models
from django.utils import timezone


class DailyPost(models.Model):
    series_title = models.CharField(max_length=280, default='No Title')
    personal_question = models.TextField()
    theme = models.TextField(default='No Theme')
    opening_hook = models.CharField(max_length=280)
    biblical_qa = models.TextField()
    reflection = models.TextField()
    story = models.TextField()
    prayer = models.TextField()
    activity_guide = models.TextField()
    date_posted = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_posted", "-created_at"]

    def __str__(self) -> str:
        return f"DailyPost({self.id}) {self.date_posted}"


class DailyDevotion(models.Model):
    # cover_image = models.ImageField(upload_to="devotions/")
    citation = models.CharField(max_length=200)  # "Sitation/Bible verse"
    verse_content = models.TextField()
    date_posted = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_posted", "-created_at"]

    def __str__(self) -> str:
        return f"DailyDevotion({self.id}) {self.date_posted}"


class Hymn(models.Model):
    hymn_number = models.PositiveIntegerField(
        help_text="Numeric identifier for the hymn")
    hymn_title = models.CharField(
        max_length=255, help_text="Title of the hymn")
    classification = models.CharField(
        max_length=100, help_text="Hymn classification or category")
    tune_ref = models.CharField(
        max_length=100, help_text="Tune reference for the hymn")
    cross_ref = models.CharField(
        max_length=255, blank=True, help_text="Cross references to related hymns")
    scripture = models.CharField(
        max_length=255, blank=True, help_text="Primary scripture reference")
    chorus_title = models.CharField(
        max_length=255, blank=True, help_text="Title of the chorus (if applicable)")
    chorus = models.TextField(blank=True, help_text="Chorus text")
    verses = models.JSONField(default=list, blank=True,
                              help_text="Ordered list of hymn verses")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-hymn_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["hymn_number"],
                name="unique_hymn_number"
            )
        ]

    def __str__(self) -> str:
        return f"#{self.hymn_number} — {self.hymn_title}"
