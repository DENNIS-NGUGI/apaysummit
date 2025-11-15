from django.contrib import admin
from django.contrib import admin
from .models import UserProfile, Participant, Invoice, InvoiceItem
from django.utils.html import format_html
from datetime import date

# Register your models here.
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
        'status_badge', 
        'issue_date', 
        'due_date',
        'payment_status'
    ]
    list_filter = ['status', 'issue_date', 'due_date', 'payment_date']
    search_fields = ['invoice_number', 'user__username', 'user__email', 'payment_reference']
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline, ParticipantInline]
    fieldsets = [
        ('Basic Information', {
            'fields': ['invoice_number', 'user', 'status', 'issue_date', 'due_date']
        }),
        ('Payment Information', {
            'fields': ['payment_date', 'payment_reference', 'subtotal', 'tax_amount', 'total_amount']
        }),
        ('Additional Information', {
            'fields': ['notes', 'created_at', 'updated_at']
        }),
    ]
    actions = ['mark_as_paid', 'mark_as_pending', 'mark_as_overdue']

    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'

    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'paid': 'success',
            'overdue': 'danger',
            'cancelled': 'secondary'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_status(self, obj):
        if obj.status == 'paid' and obj.payment_date:
            return f"Paid on {obj.payment_date}"
        elif obj.status == 'paid':
            return "Paid"
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
