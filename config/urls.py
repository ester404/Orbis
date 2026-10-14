"""
URLS do projeto inteiro. Aqui juntamos:
- o admin pronto do Django
- as telas de login/logout prontas do Django
- as URLs do nosso app "sinistros"
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="sinistros/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("sinistros.urls")),
]
