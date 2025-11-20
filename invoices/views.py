from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa
import uuid
from datetime import date, timedelta
from django.contrib import messages
from .forms import UserRegistrationForm, ParticipantForm, MultipleParticipantForm, AdminPaymentForm, EmailAuthenticationForm
from .models import Invoice, InvoiceItem, Participant, UserProfile
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from .forms import ProofOfPaymentForm, AdminPaymentVerificationForm
import csv



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Generate verification token and send email
            verification_token = user.userprofile.generate_verification_token()
            send_verification_email(user, verification_token)
            
            messages.success(request, f'Registration successful! Please check your email ({user.email}) to verify your account before logging in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'invoices/register.html', {'form': form})

def send_verification_email(user, verification_token):
    """Send verification email to user"""
    verification_url = f"{settings.SITE_URL}/invoices/verify-email/{verification_token}/"
    
    subject = 'Verify Your Email - Apay Summit Registration'
    message = f'''
    Hello {user.username},
    
    Thank you for registering with Apay Summit Registration System!
    
    Please verify your email address by clicking the link below:
    
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    Apay Summit Team
    '''
    
    html_message = render_to_string('invoices/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=html_message,
    )

def verify_email(request, token):
    """Verify user's email address"""
    try:
        profile = UserProfile.objects.get(verification_token=token)
        
        # Check if token is expired (24 hours)
        if profile.verification_sent_at and timezone.now() > profile.verification_sent_at + timedelta(hours=24):
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('login')
        
        # Mark email as verified
        profile.email_verified = True
        profile.verification_token = ''  # Clear the token
        profile.save()
        
        messages.success(request, 'Email verified successfully! You can now log in to your account.')
        return redirect('login')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link. Please try registering again.')
        return redirect('register')

def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.userprofile.email_verified:
                messages.info(request, 'Your email is already verified. You can log in.')
                return redirect('login')
            
            # Generate new verification token
            verification_token = user.userprofile.generate_verification_token()
            send_verification_email(user, verification_token)
            
            messages.success(request, f'Verification email sent to {email}. Please check your inbox.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'invoices/resend_verification.html')

def user_login(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        
        if not username_or_email or not password:
            return render(request, 'invoices/login.html', {
                'error': 'Please enter both username/email and password.'
            })
        
        # Check if input is email
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                return render(request, 'invoices/login.html', {
                    'error': 'No account found with this email address.'
                })
        else:
            username = username_or_email
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if email is verified
            if not user.userprofile.email_verified:
                messages.error(request, 'Please verify your email address before logging in. Check your email for the verification link.')
                return render(request, 'invoices/login.html', {
                    'show_resend_option': True,
                    'email': user.email
                })
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            return render(request, 'invoices/login.html', {
                'error': 'Invalid credentials. Please try again.'
            })
    
    return render(request, 'invoices/login.html')

def send_welcome_email(user):
    """Send welcome email to new user"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = 'Welcome to Apay Summit Registration System'
    message = f'''
    Hello {user.username},
    
    Welcome to the Apay Summit Registration System!
    
    Your account has been successfully created.
    
    You can now:
    - Register participants for the summit
    - Generate invoices
    - Track your payments
    
    If you have any questions, please contact our support team.
    
    Best regards,
    Apay Summit Team
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

# Allow login with both username and email
def user_login_universal(request):
    if request.method == 'POST':
        username_or_email = request.POST['username_or_email']
        password = request.POST['password']
        
        # Check if input is email
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                return render(request, 'invoices/login.html', {
                    'error': 'No account found with this email address.'
                })
        else:
            username = username_or_email
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            return render(request, 'invoices/login.html', {
                'error': 'Invalid credentials. Please try again.'
            })
    
    return render(request, 'invoices/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.is_staff:
        # Admin dashboard with system stats
        from django.contrib.auth.models import User
        from django.db.models import Sum
        
        total_users = User.objects.count()
        total_invoices = Invoice.objects.count()
        pending_invoices = Invoice.objects.filter(status__in=['pending', 'overdue']).count()
        total_revenue = Invoice.objects.filter(status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        context = {
            'total_users': total_users,
            'total_invoices': total_invoices,
            'pending_invoices': pending_invoices,
            'total_revenue': total_revenue,
        }
    else:
        # Normal user dashboard (existing code)
        invoices = Invoice.objects.filter(user=request.user).order_by('status', '-issue_date')
        participants = Participant.objects.filter(user=request.user)
        
        total_participants = participants.count()
        latest_unpaid_invoice = invoices.filter(status__in=['pending', 'overdue']).first()
        latest_invoice = invoices.first()
        unpaid_invoices = invoices.filter(status__in=['pending', 'overdue'])
        current_amount_due = sum(invoice.total_amount for invoice in unpaid_invoices)
        
        context = {
            'invoices': invoices,
            'participants': participants,
            'total_participants': total_participants,
            'latest_invoice': latest_invoice,
            'latest_unpaid_invoice': latest_unpaid_invoice,
            'current_amount_due': current_amount_due,
            'unpaid_invoices_count': unpaid_invoices.count(),
        }
    
    return render(request, 'invoices/dashboard.html', context)

@login_required
def add_participant(request):
    single_form = ParticipantForm()
    multiple_form = MultipleParticipantForm()
    
    if request.method == 'POST':
        if 'single_submit' in request.POST:
            single_form = ParticipantForm(request.POST)
            if single_form.is_valid():
                participant = single_form.save(commit=False)
                participant.user = request.user
                participant.save()
                
                # Get existing invoices for this user
                existing_invoices = Invoice.objects.filter(user=request.user)
                
                # Check if there's an unpaid invoice we can add to
                unpaid_invoice = existing_invoices.filter(status='pending').first()
                
                if unpaid_invoice:
                    # Add participant to existing unpaid invoice
                    unpaid_invoice.participants.add(participant)
                    # Update invoice amounts
                    update_invoice_amounts(unpaid_invoice)
                    messages.success(request, 'Participant added successfully! Existing invoice updated.')
                else:
                    # Create new invoice for this user
                    invoice = create_invoice(request.user)
                    # Add participant to invoice
                    invoice.participants.add(participant)
                    # Update invoice amounts
                    update_invoice_amounts(invoice)
                    messages.success(request, 'Participant added successfully! New invoice generated.')
                
                return redirect('dashboard')
                
        elif 'multiple_submit' in request.POST:
            multiple_form = MultipleParticipantForm(request.POST)
            if multiple_form.is_valid():
                participants_data = multiple_form.cleaned_data['participants_data']
                lines = participants_data.strip().split('\n')
                added_count = 0
                errors = []
                
                # Get existing invoices for this user
                existing_invoices = Invoice.objects.filter(user=request.user)
                unpaid_invoice = existing_invoices.filter(status='pending').first()
                
                # If no unpaid invoice exists, create one
                if not unpaid_invoice:
                    unpaid_invoice = create_invoice(request.user)
                
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line:
                        parts = [part.strip() for part in line.split(',')]
                        if len(parts) == 3:
                            name, email, phone = parts
                            if name and email:  # Basic validation
                                participant = Participant(
                                    user=request.user,
                                    name=name,
                                    email=email,
                                    phone=phone
                                )
                                participant.save()
                                unpaid_invoice.participants.add(participant)
                                added_count += 1
                            else:
                                errors.append(f"Line {i}: Name and email are required")
                        else:
                            errors.append(f"Line {i}: Invalid format. Expected: Name,Email,Phone")
                
                # Update invoice amounts
                update_invoice_amounts(unpaid_invoice)
                
                if added_count > 0:
                    messages.success(request, f'Successfully added {added_count} participants! Invoice updated.')
                if errors:
                    for error in errors:
                        messages.warning(request, error)
                
                return redirect('dashboard')
    
    context = {
        'single_form': single_form,
        'multiple_form': multiple_form,
    }
    return render(request, 'invoices/add_participant.html', context)

def format_currency(value):
    """Format currency with commas for PDF"""
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return str(value)

def custom_404(request, exception):
    return render(request, 'invoices/404.html', status=404)

def format_currency(value):
    """Format currency with commas for PDF"""
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return str(value)
    
@login_required
def download_invoice_pdf(request, invoice_id):
    # Allow staff users to download any invoice, regular users only their own
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    # Format currency amounts for PDF WITHOUT overwriting originals
    # Add formatted versions as new attributes
    invoice.subtotal_formatted = format_currency(invoice.subtotal)
    invoice.tax_amount_formatted = format_currency(invoice.tax_amount)
    invoice.total_amount_formatted = format_currency(invoice.total_amount)

    # Format items without overwriting originals
    for item in invoice.items.all():
        item.unit_price_formatted = format_currency(item.unit_price)
        item.total_formatted = format_currency(item.total)
    
    # Logo URL    
    logo_url = "https://icta.go.ke//assets/images/ictalogo.png"  

    # Render HTML template with logo URL
    html_string = render_to_string('invoices/invoice_pdf.html', {
        'invoice': invoice,
        'logo_url': logo_url
    })
    
    # Create PDF using xhtml2pdf
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=500)

def calculate_pricing(participant_count):
    """Calculate pricing based on participant count"""
    if participant_count <= 3:
        return 15000 * participant_count
    elif participant_count == 4:
        return 45000
    else:  # More than 4
        return 11000 * participant_count

def get_or_create_invoice(user):
    """Get existing invoice or create new one for user"""
    invoices = Invoice.objects.filter(user=user)
    
    if invoices.exists():
        # Return the latest invoice
        return invoices.first()
    else:
        # Create new invoice
        return create_invoice(user)

def create_invoice(user):
    """Create a new invoice for user"""
    invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    invoice = Invoice.objects.create(
        invoice_number=invoice_number,
        user=user,
        due_date=date.today() + timedelta(days=30),
        status='pending',
        subtotal=0.00,
        tax_amount=0.00,
        total_amount=0.00,
        notes="Apay Summit Registration"
    )
    
    return invoice

def update_invoice_amounts(invoice):
    """Update invoice amounts based on participants"""
    participant_count = invoice.participants.count()
    
    if participant_count == 0:
        # No participants, set amounts to zero
        invoice.subtotal = 0.00
        invoice.tax_amount = 0.00
        invoice.total_amount = 0.00
        invoice.notes = "Add participants to generate invoice"
    else:
        # Calculate amounts based on participants
        subtotal = calculate_pricing(participant_count)
        tax_amount = 0.00  # VAT is exclusive
        total_amount = subtotal + tax_amount
        
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        
        # Update notes based on pricing structure
        if participant_count <= 3:
            invoice.notes = f"Payment for {participant_count} participant(s) - Individual Rate (KES 15,000 per person)"
        elif participant_count == 4:
            invoice.notes = f"Payment for {participant_count} participant(s) - Special Group Rate (KES 45,000 total)"
        else:
            invoice.notes = f"Payment for {participant_count} participant(s) - Group Rate (KES 11,000 per person)"
    
    invoice.save()
    
    # Update or create invoice items
    update_invoice_items(invoice, participant_count)

def update_invoice_items(invoice, participant_count):
    """Update invoice items based on participant count and pricing"""
    # Clear existing items
    invoice.items.all().delete()
    
    if participant_count == 0:
        return
    
    # Add main registration item
    if participant_count <= 3:
        description = f"Individual Registration - {participant_count} participant(s)"
        unit_price = 15000
    elif participant_count == 4:
        description = "Group Registration - 4 participants (Special Rate)"
        unit_price = 11250  # 45000 / 4
    else:
        description = f"Group Registration - {participant_count} participant(s)"
        unit_price = 11000
    
    InvoiceItem.objects.create(
        invoice=invoice,
        description=description,
        quantity=participant_count,
        unit_price=unit_price,
        total=invoice.subtotal
    )

@login_required
def participants_list(request):
    participants = Participant.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'participants': participants,
        'total_participants': participants.count(),
    }
    return render(request, 'invoices/participants_list.html', context)

@staff_member_required
def admin_update_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = AdminPaymentForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payment status updated for invoice {invoice.invoice_number}')
            return redirect('admin_invoice_list')
    else:
        form = AdminPaymentForm(instance=invoice)
    
    context = {
        'form': form,
        'invoice': invoice,
    }
    return render(request, 'invoices/admin_update_payment.html', context)

@login_required
def invoice_detail(request, invoice_id):
    # Allow staff users to view any invoice, regular users only their own
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    # Check if invoice can be modified
    can_add_participants = invoice.can_add_participants()
    
    proof_form = ProofOfPaymentForm(instance=invoice)
    
    if request.method == 'POST' and 'upload_proof' in request.POST:
        proof_form = ProofOfPaymentForm(request.POST, request.FILES, instance=invoice)
        if proof_form.is_valid():
            proof_form.save()
            messages.success(request, 'Proof of payment uploaded successfully! Our team will review it shortly.')
            return redirect('invoice_detail', invoice_id=invoice_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    context = {
        'invoice': invoice,
        'can_add_participants': can_add_participants,
        'proof_form': proof_form,
    }
    return render(request, 'invoices/invoice.html', context)

@login_required
def invoices_list(request):
    invoices = Invoice.objects.filter(user=request.user).order_by('-issue_date')
    
    # Calculate totals
    total_invoices = invoices.count()
    unpaid_invoices = invoices.filter(status__in=['pending', 'overdue'])
    total_due = sum(invoice.total_amount for invoice in unpaid_invoices)
    
    # Create forms for each invoice
    invoice_forms = {}
    for invoice in invoices:
        invoice_forms[invoice.id] = ProofOfPaymentForm(instance=invoice)
    
    if request.method == 'POST' and 'upload_proof' in request.POST:
        invoice_id = request.POST.get('invoice_id')
        invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
        proof_form = ProofOfPaymentForm(request.POST, request.FILES, instance=invoice)
        if proof_form.is_valid():
            proof_form.save()
            messages.success(request, f'Proof of payment uploaded for invoice {invoice.invoice_number}! Our team will review it shortly.')
            return redirect('invoices_list')
        else:
            messages.error(request, 'Please correct the errors below.')
            # Update the form for this specific invoice
            invoice_forms[invoice.id] = proof_form
    
    context = {
        'invoices': invoices,
        'total_invoices': total_invoices,
        'unpaid_invoices_count': unpaid_invoices.count(),
        'total_due': total_due,
        'invoice_forms': invoice_forms,
    }
    return render(request, 'invoices/invoices_list.html', context)

@staff_member_required
def admin_invoice_list(request):
    invoices = Invoice.objects.all().order_by('-issue_date')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            models.Q(invoice_number__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(user__email__icontains=search_query) |
            models.Q(payment_reference__icontains=search_query)
        )
    
    # Create admin forms for each invoice
    admin_forms = {}
    for invoice in invoices:
        admin_forms[invoice.id] = AdminPaymentVerificationForm(instance=invoice)
    
    if request.method == 'POST' and 'verify_payment' in request.POST:
        invoice_id = request.POST.get('invoice_id')
        invoice = get_object_or_404(Invoice, id=invoice_id)
        admin_form = AdminPaymentVerificationForm(request.POST, instance=invoice)
        if admin_form.is_valid():
            admin_form.save()
            messages.success(request, f'Payment status updated for invoice {invoice.invoice_number}!')
            return redirect('admin_invoice_list')
        else:
            messages.error(request, 'Please correct the errors below.')
            admin_forms[invoice.id] = admin_form
    
    context = {
        'invoices': invoices,
        'status_filter': status_filter,
        'search_query': search_query,
        'admin_forms': admin_forms,
    }
    return render(request, 'invoices/admin_invoice_list.html', context)

@staff_member_required
def admin_update_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = AdminPaymentVerificationForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payment status updated for invoice {invoice.invoice_number}!')
            return redirect('admin_invoice_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPaymentVerificationForm(instance=invoice)
    
    context = {
        'invoice': invoice,
        'form': form,
    }
    return render(request, 'invoices/admin_update_payment.html', context)

@login_required
def help_manual(request):
    """Main help manual page"""
    return render(request, 'help/help_manual.html')

@login_required
def getting_started(request):
    """Getting started guide"""
    return render(request, 'help/getting_started.html')

@login_required
def invoice_guide(request):
    """Invoice management guide"""
    return render(request, 'help/invoice_guide.html')

@login_required
def payment_guide(request):
    """Payment process guide"""
    return render(request, 'help/payment_guide.html')

def export_participants_pdf(participants, user_summary, participant_invoices_map, total_paid_all_users, request_user):
    """Export participants data to PDF"""
    from io import BytesIO
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    html_string = render_to_string('invoices/participants_pdf_report.html', {
        'participants': participants,
        'user_summary': user_summary,
        'total_participants': len(participants),
        'total_users': len(user_summary),
        'total_paid_all_users': total_paid_all_users,  # NEW: Pass total paid amount
        'report_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'generated_by': request_user,
    })
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="participants_report.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=500)


def export_participants_csv(participants, participant_invoices_map, total_paid_all_users):
    """Export participants data to CSV"""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="participants_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Participant Name', 'Email', 'Phone', 'Registered By', 
        'User Email', 'Invoice Count', 'Invoice Status', 'Total Amount',
        'Paid Amount', 'Registration Date'  # ADDED: Paid Amount
    ])
    
    for participant in participants:
        user = participant.user
        invoices = participant_invoices_map.get(participant.id, [])
        invoice_count = len(invoices)
        invoice_status = ", ".join([inv.get_status_display() for inv in invoices]) if invoices else "No Invoice"
        total_amount = sum(inv.total_amount for inv in invoices) if invoices else 0
        paid_amount = sum(inv.total_amount for inv in invoices if inv.status == 'paid') if invoices else 0  # NEW: Paid amount
        
        writer.writerow([
            participant.name,
            participant.email,
            participant.phone,
            user.username,
            user.email,
            invoice_count,
            invoice_status,
            total_amount,
            paid_amount,  # NEW: Paid amount
            participant.created_at.strftime('%Y-%m-%d')
        ])
    
    # Add summary row
    writer.writerow([])
    writer.writerow(['SUMMARY', '', '', '', '', '', '', '', ''])
    writer.writerow(['Total Participants', len(participants)])
    writer.writerow(['Total Paid Amount (All Users)', f"KES {total_paid_all_users:,.2f}"])
    
    return response


@staff_member_required
def admin_participants_list(request):
    # Get all participants with related user data
    participants = Participant.objects.all().select_related('user')
    
    # Filtering
    user_filter = request.GET.get('user', '')
    if user_filter:
        participants = participants.filter(user__username__icontains=user_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        participants = participants.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone__icontains=search_query) |
            models.Q(user__username__icontains=search_query)
        )
    
    # Calculate statistics
    total_participants = participants.count()
    total_users = User.objects.filter(participants__isnull=False).distinct().count()
    
    # Get users with their paid invoices
    users_with_counts = User.objects.filter(
        participants__isnull=False
    ).annotate(
        participant_count=models.Count('participants')
    ).distinct()
    
    user_summary = {}
    for user in users_with_counts:
        user_invoices = Invoice.objects.filter(user=user)
        paid_invoices = user_invoices.filter(status='paid')
        total_paid_amount = paid_invoices.aggregate(
            total_paid=models.Sum('total_amount')
        )['total_paid'] or 0
        
        user_summary[user.id] = {
            'user': user,
            'participant_count': user.participant_count,
            'total_invoices': user_invoices.count(),
            'paid_invoices': paid_invoices.count(),
            'total_amount': user_invoices.aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0,
            'total_paid_amount': total_paid_amount,  # NEW: Total paid amount
        }
    
    # Get invoices for each participant
    all_invoices = Invoice.objects.prefetch_related('participants')
    participant_invoices_map = {}
    
    for invoice in all_invoices:
        for participant in invoice.participants.all():
            if participant.id not in participant_invoices_map:
                participant_invoices_map[participant.id] = []
            participant_invoices_map[participant.id].append(invoice)
    
    # Add invoices to each participant for template use
    for participant in participants:
        participant.invoice_list = participant_invoices_map.get(participant.id, [])
    
    # Calculate total paid amount across all users
    total_paid_all_users = sum(summary['total_paid_amount'] for summary in user_summary.values())
    
    # Export functionality
    export_format = request.GET.get('export', '')
    if export_format == 'csv':
        return export_participants_csv(participants, participant_invoices_map, total_paid_all_users)
    elif export_format == 'pdf':
        return export_participants_pdf(participants, user_summary, participant_invoices_map, total_paid_all_users, request.user)
    
    context = {
        'participants': participants,
        'user_summary': user_summary,
        'total_participants': total_participants,
        'total_users': total_users,
        'total_paid_all_users': total_paid_all_users,  # NEW: Total paid for all users
        'user_filter': user_filter,
        'search_query': search_query,
    }
    return render(request, 'invoices/admin_participants_list.html', context)