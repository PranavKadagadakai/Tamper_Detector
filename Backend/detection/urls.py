from django.urls import path
from detection.views import RegisterView, LoginView, UploadView, HistoryView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("history/", HistoryView.as_view(), name="history"),
]
