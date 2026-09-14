from django.db import models
from django.conf import settings

# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    tags = models.ManyToManyField(Tag, blank=True)

    # AI-related tracking fields (optional — remove if you don't need auditing)
    ai_generated = models.BooleanField(default=False)
    ai_prompt = models.TextField(blank=True, help_text="Prompt used to generate/edit this post")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
    


