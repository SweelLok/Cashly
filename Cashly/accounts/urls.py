from django.urls import path
from .views import activate_email, register_view, login_view, logout_view, dashboard_view


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
	path('activate/<uidb64>/<token>/', activate_email, name='activate'),
]
