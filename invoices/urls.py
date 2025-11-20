from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy


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

    # Help manual URLs
    path('help/', views.help_manual, name='help_manual'),
    path('help/getting-started/', views.getting_started, name='getting_started'),
    path('help/invoices/', views.invoice_guide, name='invoice_guide'),
    path('help/payments/', views.payment_guide, name='payment_guide'),
    
    # Admin URLs
    path('admin/invoices/', views.admin_invoice_list, name='admin_invoice_list'),
    path('admin/invoice/<int:invoice_id>/update-payment/', views.admin_update_payment, name='admin_update_payment'),
    path('admin/participants/', views.admin_participants_list, name='admin_participants_list'),
    
    # Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url=reverse_lazy('password_reset_done')
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')  # This will work correctly
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

