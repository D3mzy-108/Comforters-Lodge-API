from django.db import models
from django.utils import timezone

class DailyPost(models.Model):
    opening_hook = models.CharField(max_length=280)
    personal_question = models.TextField()
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
