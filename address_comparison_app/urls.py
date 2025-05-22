# urls.py: URL routing for the hello app, following Django best practices.
from django.urls import path
from .views import health_check, mongo_query_view

urlpatterns = [
    path('', health_check, name='health_check'),  # Health check or landing page
    path('mongo/', mongo_query_view, name='mongo_query'),
]
