from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/me/', views.me, name='me'),
    path('api/login/', views.login_patient, name='login_patient'),
    path('api/logout/', views.logout_patient, name='logout_patient'),
    path('api/profile/delete/', views.delete_profile, name='delete_profile'),
    path('api/posts/', views.posts, name='posts'),
    path('api/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('api/rooms/', views.rooms, name='rooms'),
    path('api/rooms/<int:patient_id>/', views.room_detail, name='room_detail'),
]
