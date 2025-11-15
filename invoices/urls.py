from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-participant/', views.add_participant, name='add_participant'),
    path('participants/', views.participants_list, name='participants_list'),
    path('invoices/', views.invoices_list, name='invoices_list'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/download/', views.download_invoice_pdf, name='download_invoice'),
    
    # Admin URLs
    path('admin/invoices/', views.admin_invoice_list, name='admin_invoice_list'),
    path('admin/invoice/<int:invoice_id>/update-payment/', views.admin_update_payment, name='admin_update_payment'),
]