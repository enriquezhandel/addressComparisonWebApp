# urls.py: URL routing for the hello app, following Django best practices.
from django.urls import path
from .views import hello_world, mongo_query_view

urlpatterns = [
    path('', hello_world, name='hello_world'),  # Health check or landing page
    path('mongo/', mongo_query_view, name='mongo_query'),  # Main MongoDB query UI
]
