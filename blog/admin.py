from django.contrib import admin
from . models import Post, Tag

# Register your models here.


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "author", "created_at")
    list_filter = ("status", "tags", "created_at", "published_at")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    # readonly_fields = ("ai_generated",)


admin.site.register(Tag)
