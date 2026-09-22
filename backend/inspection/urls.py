from django.urls import path

from inspection import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.list_view, name="list"),
    path("sections/", views.sections_view, name="sections"),
    path("inspections/new/", views.create_view, name="create"),
    path("inspections/<int:pk>/", views.detail_view, name="detail"),
    path("inspections/<int:pk>/tag/", views.tag_view, name="tag"),
]
