# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('',views.landing_page.as_view(), name='landing'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.custom_login, name='login'),
    path('update/<int:pk>/profile/', views.UserUpdateView.as_view(), name="updateProfile"),
    path('dashboard/', views.dashboard.as_view(), name='dashboard'),
    path('accounts/logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('vehicle/add/',views.VehicleCreateView.as_view(), name='addVehicle'),
    path('ajax/load-models/', views.load_models, name='ajaxLoadmodels'),
    path('sparepart/add', views.SparepartCreateView.as_view(), name='addSparepart'),
    path('ajax/load-subtypes/', views.load_subtypes, name='ajaxLoadSubtypes'),
    path('service/add',views.ServiceCreateView.as_view(), name='addService'),
    path('ajax/load-subservices', views.load_subtypeofservice, name='ajaxLoadsubservices'),
    path('vehicle/<int:pk>/edit', views.VehicleUpdateView.as_view(), name='editVehicle'),
    path('vehicle/<int:pk>/delete', views.VehicleDeleteView.as_view(), name='deleteVehicle'),
    path('sparepart/<int:pk>/edit', views.SparepartUpdateView.as_view(), name='editSparepart'),
    path('sparepart/<int:pk>/delete', views.SparepartDeleteView.as_view(), name='deleteSparepart'),
    path('service/<int:pk>/edit',views.ServiceUpdateView.as_view(), name='editService'),
    path('service/<int:pk>/delete', views.ServiceDeleteView.as_view(), name='deleteService'),
    path('otp-email/', views.OTPEmailView.as_view(), name='otp-email'),
    path('otp-verify/', views.OTPVerifyView.as_view(), name='otp-verify'),
    path('vehicle/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('sparepart/<int:pk>/', views.SparePartDetailView.as_view(), name='sparepart_detail'),
    path('service/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('user/<int:pk>/listings/', views.UserListingsView.as_view(), name='user_listings'),
    


    # You can also add paths for password reset/change using Django's built-in views.
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
