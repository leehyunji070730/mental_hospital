from django.urls import include, path

urlpatterns = [
    path('', include('ward.urls')),
]
