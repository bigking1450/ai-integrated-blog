from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.home_page, name="home-page"),
    path("posts", views.all_posts, name="all-posts-page"),
    path("posts/mine/", views.my_posts, name="my-posts"),
    path("posts/add-post", views.add_post, name="add-post-page"),
    path("posts/generate/", views.generate_post_draft, name="generate-post-draft"),
    path("posts/edit/<slug:slug>", views.edit_post, name="edit-post"),
    path("posts/<slug:slug>/delete/", views.delete_post, name="delete-post"),
    path("posts/<slug:slug>/", views.view_post, name="post-detail-page"),
    path("posts/<slug:slug>/toggle-status/", views.toggle_post_status, name="toggle-post-status"),
    path("accounts/login/", LoginView.as_view(template_name="blog/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(next_page="home-page"), name="logout"),
    path("accounts/register/", views.register_view, name="register"),
]
