from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.text import slugify
# from django.http import HttpResponseForbidden

from .models import Post
from .forms import AddPostForm, AIGenerateForm, RegisterForm
from .services import generate_post, edit_post_content, AIServiceError

# def get_date(post):
#     return post['date']

# Create your views here.
def home_page(request):
    latest_posts = Post.objects.all().order_by("-created_at")[:3]
    return render(request, "blog/index.html", {"posts": latest_posts})


def all_posts(request):
    post_list = Post.objects.filter(status="published").order_by("-created_at")
    paginator = Paginator(post_list, 9)  # 9 per page
    page_number = request.GET.get("page")
    all_posts = paginator.get_page(page_number)
    return render(request, "blog/all-posts.html", {"all_posts": all_posts})


def view_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    tags = post.tags.all()
    return render(request, "blog/post-detail.html", {"post": post, "tags": tags})


@login_required
def add_post(request):
    if request.method == 'POST':
        form = AddPostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            SLUG_MAX_LENGTH = 50  # matches your model's SlugField max_length

            base_slug = slugify(post.title)[:SLUG_MAX_LENGTH]
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                suffix = f"-{counter}"
                slug = f"{base_slug[:SLUG_MAX_LENGTH - len(suffix)]}{suffix}"
                counter += 1
            post.slug = slug

            post.save()
            form.save_m2m()
            return redirect("all-posts-page")
    else:
        ai_draft = request.session.pop("ai_draft", None)  # pop() clears it after reading
        form = AddPostForm(initial=ai_draft) if ai_draft else AddPostForm()

    return render(request, "blog/post-form.html", {"form": form})


@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user:
        messages.error(request, "You don't have permission to edit this post.")
        return redirect("post-detail-page", slug=post.slug)

    if request.method == 'POST':
        if request.POST.get("action") == "refine":
            instruction = request.POST.get("instruction", "").strip()
            if not instruction:
                messages.error(request, "Please enter an instruction for the AI.")
                return render(request, "blog/post-form.html", {"form": AddPostForm(instance=post), "post": post})

            try:
                revised_body = edit_post_content(post.body, instruction)
            except AIServiceError as e:
                messages.error(request, f"AI refinement failed: {e}")
                return render(request, "blog/post-form.html", {"form": AddPostForm(instance=post), "post": post})

            # Show the AI's suggestion in the form WITHOUT saving — user must submit normally to accept it
            form = AddPostForm(instance=post, initial={"body": revised_body})
            messages.info(request, "AI suggestion loaded below — review before saving.")
            return render(request, "blog/post-form.html", {"form": form, "post": post})

        # Normal save path (unchanged from before)
        form = AddPostForm(request.POST, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)

            if updated_post.title != post.title:
                base_slug = slugify(updated_post.title)
                new_slug = base_slug
                counter = 1
                while Post.objects.filter(slug=new_slug).exclude(pk=post.pk).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                updated_post.slug = new_slug

            updated_post.save()
            form.save_m2m()
            return redirect("post-detail-page", slug=updated_post.slug)
    else:
        form = AddPostForm(instance=post)

    return render(request, "blog/post-form.html", {"form": form, "post": post})


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    # Only the original author can delete their own post
    if post.author != request.user:
        messages.error(request, "You don't have permission to delete this post.")
        return redirect("post-detail-page", slug=post.slug)

    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully.")
        return redirect("all-posts-page")

    # GET request: show a confirmation page before actually deleting
    return render(request, "blog/post-confirm-delete.html", {"post": post})


@login_required
def generate_post_draft(request):
    if request.method == 'POST':
        form = AIGenerateForm(request.POST)
        if form.is_valid():
            try:
                result = generate_post(
                    topic=form.cleaned_data["topic"],
                    tone=form.cleaned_data.get("tone") or "informative and engaging",
                )
            except AIServiceError as e:
                messages.error(request, f"AI generation failed: {e}")
                return render(request, "blog/ai-generate.html", {"form": form})

            request.session["ai_draft"] = result  # stash for add_post to pick up
            return redirect("add-post-page")
    else:
        form = AIGenerateForm()

    return render(request, "blog/ai-generate.html", {"form": form})


@login_required
def my_posts(request):
    post_list = Post.objects.filter(author=request.user).order_by("-created_at")
    paginator = Paginator(post_list, 10)  # 10 per page
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)
    return render(request, "blog/my-posts.html", {"posts": posts})


@login_required
@require_POST
def toggle_post_status(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user:
        messages.error(request, "You don't have permission to change this post's status.")
        return redirect("my-posts")

    if post.status == "draft":
        post.status = "published"
        if post.published_at is None:
            post.published_at = timezone.now()
    else:
        post.status = "draft"

    post.save()
    messages.success(request, f"\"{post.title}\" is now {post.get_status_display().lower()}.")
    return redirect("my-posts")


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the user in immediately after registering
            messages.success(request, "Account created successfully. Welcome!")
            return redirect("home-page")
    else:
        form = RegisterForm()

    return render(request, "blog/register.html", {"form": form})