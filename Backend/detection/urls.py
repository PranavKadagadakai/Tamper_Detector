from django.urls import path
from .views import RegisterView, HistoryView, LoginView, UploadImageView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("upload/", UploadImageView.as_view()),
    path("history/", HistoryView.as_view()),
]