from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from django import forms
from .models import Post


class AddPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "excerpt", "body", "tags"]
        labels = {
            "title": "Post Title",
            "excerpt": "Intro",
            "body": "Post Content",
            "tags": "Tags"
        }
        widgets = {
            "tags": forms.CheckboxSelectMultiple(),  # or SelectMultiple for a dropdown
        }


class AIGenerateForm(forms.Form):
    topic = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Getting started with Django signals"})
    )
    tone = forms.CharField(
        max_length=100,
        required=False,
        initial="informative and engaging",
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "password1", "password2"]
