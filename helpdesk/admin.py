from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CustomUser, TicketCategory, TriggerRule, Ticket, 
    TicketHistory, TicketComment, TicketAttachment, Notification
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom user admin with role management"""
    
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'company')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Helpdesk Info', {
            'fields': ('role', 'phone_number', 'department', 'company')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Helpdesk Info', {
            'fields': ('role', 'phone_number', 'department', 'company')
        }),
    )


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    """Ticket category admin"""
    
    list_display = ('name', 'description', 'color_display', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(TriggerRule)
class TriggerRuleAdmin(admin.ModelAdmin):
    """Trigger rule admin"""
    
    list_display = ('name', 'action', 'category', 'is_active', 'created_at')
    list_filter = ('action', 'is_active', 'category', 'created_at')
    search_fields = ('name', 'keywords')
    filter_horizontal = ('notify_users',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'keywords', 'action', 'category', 'is_active')
        }),
        ('Notifications', {
            'fields': ('notify_users',),
            'classes': ('collapse',)
        }),
    )


class TicketHistoryInline(admin.TabularInline):
    """Inline for ticket history"""
    model = TicketHistory
    extra = 0
    readonly_fields = ('action_type', 'actor', 'description', 'old_value', 'new_value', 'timestamp')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class TicketCommentInline(admin.StackedInline):
    """Inline for ticket comments"""
    model = TicketComment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class TicketAttachmentInline(admin.TabularInline):
    """Inline for ticket attachments"""
    model = TicketAttachment
    extra = 0
    readonly_fields = ('file_name', 'file_size', 'uploaded_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Comprehensive ticket admin"""
    
    list_display = (
        'ticket_number', 'subject', 'status_badge', 'priority_badge', 
        'category', 'created_by', 'assigned_to', 'created_at'
    )
    list_filter = (
        'status', 'priority', 'severity', 'category', 'is_escalated',
        'created_at', 'assigned_to__role'
    )
    search_fields = (
        'ticket_number', 'subject', 'description', 
        'created_by__username', 'assigned_to__username'
    )
    readonly_fields = (
        'ticket_number', 'created_at', 'updated_at', 'resolved_at', 
        'closed_at', 'escalated_at'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ticket_number', 'subject', 'description', 'category')
        }),
        ('Classification', {
            'fields': ('status', 'priority', 'severity')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Escalation', {
            'fields': ('is_escalated', 'escalated_at', 'escalated_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TicketHistoryInline, TicketCommentInline, TicketAttachmentInline]
    
    def status_badge(self, obj):
        colors = {
            'open': 'red',
            'in_progress': 'orange',
            'pending': 'yellow',
            'resolved': 'green',
            'closed': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.priority, 'gray'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'assigned_to', 'escalated_by'
        )


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    """Ticket history admin (read-only)"""
    
    list_display = ('ticket', 'action_type', 'actor', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('ticket__ticket_number', 'description', 'actor__username')
    readonly_fields = ('ticket', 'action_type', 'actor', 'description', 'old_value', 'new_value', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """Ticket comment admin"""
    
    list_display = ('ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at', 'author__role')
    search_fields = ('ticket__ticket_number', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    """Ticket attachment admin"""
    
    list_display = ('file_name', 'ticket', 'attachment_type', 'uploaded_by', 'file_size_display', 'uploaded_at')
    list_filter = ('attachment_type', 'uploaded_at')
    search_fields = ('file_name', 'ticket__ticket_number', 'description')
    readonly_fields = ('file_name', 'file_size', 'uploaded_at')
    
    def file_size_display(self, obj):
        return f"{obj.file_size_mb} MB"
    file_size_display.short_description = 'File Size'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin"""
    
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'ticket')


# Admin site customization
admin.site.site_header = "Blue River Technology Solutions - Helpdesk"
admin.site.site_title = "BRTS Helpdesk"
admin.site.index_title = "Helpdesk Administration"
