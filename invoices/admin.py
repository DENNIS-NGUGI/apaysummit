from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, Participant, Invoice, InvoiceItem
from datetime import date

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total']

class ParticipantInline(admin.TabularInline):
    model = Invoice.participants.through
    extra = 1
    verbose_name = "Participant"
    verbose_name_plural = "Participants"

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 
        'user', 
        'participants_count',
        'total_amount', 
        'status',  # Added status to list_display
        'status_badge', 
        'proof_of_payment_link',
        'issue_date', 
        'due_date',
        'payment_status'
    ]
    list_editable = ['status']  # Now status is in both list_display and list_editable
    list_filter = ['status', 'issue_date', 'due_date', 'payment_date']
    search_fields = ['invoice_number', 'user__username', 'user__email', 'payment_reference']
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at', 'proof_of_payment_display']
    inlines = [InvoiceItemInline, ParticipantInline]
    
    # Updated fieldsets to include proof of payment viewing
    fieldsets = [
        ('Basic Information', {
            'fields': ['invoice_number', 'user', 'status', 'issue_date', 'due_date']
        }),
        ('Payment Information', {
            'fields': ['payment_date', 'payment_reference', 'subtotal', 'tax_amount', 'total_amount']
        }),
        ('Proof of Payment', {
            'fields': ['proof_of_payment_display', 'proof_of_payment', 'payment_method', 'payment_notes'],
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ['notes', 'created_at', 'updated_at']
        }),
    ]
    
    actions = ['mark_as_paid', 'mark_as_under_review', 'mark_as_pending', 'mark_as_overdue']

    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'

    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'under_review': 'info',
            'paid': 'success',
            'overdue': 'danger',
            'cancelled': 'secondary'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status Badge'

    def proof_of_payment_link(self, obj):
        if obj.proof_of_payment:
            return format_html(
                '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '<i class="fas fa-eye"></i> View Proof'
                '</a>',
                obj.proof_of_payment.url
            )
        return format_html('<span style="color: #6c757d; font-size: 11px;">No proof</span>')
    proof_of_payment_link.short_description = 'Proof'

    def proof_of_payment_display(self, obj):
        if obj.proof_of_payment:
            file_extension = obj.proof_of_payment.name.split('.')[-1].lower()
            if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                return format_html(
                    '<div style="text-align: center;">'
                    '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; display: inline-block; margin-bottom: 15px;">'
                    '<i class="fas fa-external-link-alt"></i> Open Proof of Payment'
                    '</a><br>'
                    '<img src="{}" style="max-width: 300px; max-height: 300px; border: 2px solid #ddd; border-radius: 5px;">'
                    '</div>',
                    obj.proof_of_payment.url,
                    obj.proof_of_payment.url
                )
            else:
                return format_html(
                    '<div style="text-align: center;">'
                    '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 12px 24px; border-radius: 5px; text-decoration: none; display: inline-block;">'
                    '<i class="fas fa-download"></i> Download Proof of Payment'
                    '</a><br>'
                    '<small style="color: #666; margin-top: 10px; display: block;">File: {}</small>'
                    '</div>',
                    obj.proof_of_payment.url,
                    obj.proof_of_payment.name
                )
        return format_html(
            '<div style="text-align: center; color: #6c757d; padding: 20px;">'
            '<i class="fas fa-file-upload fa-2x" style="margin-bottom: 10px;"></i><br>'
            'No proof of payment uploaded'
            '</div>'
        )
    proof_of_payment_display.short_description = 'Proof of Payment Preview'

    def payment_status(self, obj):
        if obj.status == 'paid' and obj.payment_date:
            return f"Paid on {obj.payment_date}"
        elif obj.status == 'paid':
            return "Paid"
        elif obj.status == 'under_review':
            return "Under Review"
        else:
            days_until_due = (obj.due_date - date.today()).days
            if days_until_due < 0:
                return "Overdue"
            elif days_until_due == 0:
                return "Due today"
            else:
                return f"Due in {days_until_due} days"
    payment_status.short_description = 'Payment Status'

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', payment_date=date.today())
        self.message_user(request, f'{updated} invoice(s) marked as paid.')
    mark_as_paid.short_description = "Mark selected invoices as paid"

    def mark_as_under_review(self, request, queryset):
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} invoice(s) marked as under review.')
    mark_as_under_review.short_description = "Mark selected invoices as under review"

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending', payment_date=None)
        self.message_user(request, f'{updated} invoice(s) marked as pending.')
    mark_as_pending.short_description = "Mark selected invoices as pending"

    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status='overdue')
        self.message_user(request, f'{updated} invoice(s) marked as overdue.')
    mark_as_overdue.short_description = "Mark selected invoices as overdue"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'phone', 'created_at']
    search_fields = ['user__username', 'company_name', 'phone']

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'email', 'phone', 'user__username']

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']
    list_filter = ['invoice__invoice_number']
    search_fields = ['description', 'invoice__invoice_number']


