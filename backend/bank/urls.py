from django.urls import path

from bank import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("papers/generate/", views.generate_paper_view, name="generate-paper"),
    path("papers/history/", views.paper_history, name="paper-history"),
    path("papers/<int:paper_no>/", views.paper_detail, name="paper-detail"),
    path("exams/submit/", views.submit_exam, name="submit-exam"),
    path("auth/demo-login/", views.demo_login, name="demo-login"),
]
