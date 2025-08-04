from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import re


class CustomUser(AbstractUser):
    """Extended User model with roles for the helpdesk system"""
    
    USER_ROLES = [
        ('client', 'Client'),
        ('agent', 'Support Agent'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=10, choices=USER_ROLES, default='client')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_client(self):
        return self.role == 'client'
    
    @property
    def is_agent(self):
        return self.role == 'agent'
    
    @property
    def is_admin(self):
        return self.role == 'admin'


class TicketCategory(models.Model):
    """Categories for organizing tickets"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Bootstrap colors
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Ticket Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TriggerRule(models.Model):
    """Rules for auto-escalation and notifications based on keywords"""
    
    TRIGGER_ACTIONS = [
        ('escalate', 'Auto Escalate'),
        ('notify', 'Send Notification'),
        ('priority_high', 'Set High Priority'),
        ('priority_critical', 'Set Critical Priority'),
    ]
    
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Comma-separated keywords (case-insensitive)")
    action = models.CharField(max_length=20, choices=TRIGGER_ACTIONS)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, blank=True, null=True)
    notify_users = models.ManyToManyField(CustomUser, blank=True, limit_choices_to={'role__in': ['agent', 'admin']})
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_action_display()}"
    
    def get_keyword_list(self):
        """Return list of keywords for matching"""
        return [keyword.strip().lower() for keyword in self.keywords.split(',') if keyword.strip()]


class Ticket(models.Model):
    """Main ticket model with all required fields"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending Customer Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic ticket fields
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    
    # User relationships
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_tickets', limit_choices_to={'role__in': ['agent', 'admin']})
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-escalation flags
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='escalated_tickets')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate ticket number if not exists
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        
        # Auto-prioritization based on keywords
        if not self.pk:  # Only for new tickets
            self.auto_prioritize()
            self.check_trigger_rules()
        
        # Set resolved/closed timestamps
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        from django.utils import timezone
        year = timezone.now().year
        last_ticket = Ticket.objects.filter(
            ticket_number__startswith=f"BRTS-{year}"
        ).order_by('-ticket_number').first()
        
        if last_ticket:
            last_number = int(last_ticket.ticket_number.split('-')[2])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"BRTS-{year}-{new_number:04d}"
    
    def auto_prioritize(self):
        """Auto-assign priority based on keywords in subject and description"""
        text = f"{self.subject} {self.description}".lower()
        
        critical_keywords = ['critical', 'emergency', 'outage', 'down', 'breach', 'security breach', 'data loss']
        high_keywords = ['urgent', 'high', 'important', 'asap', 'immediate', 'production']
        
        if any(keyword in text for keyword in critical_keywords):
            self.priority = 'critical'
        elif any(keyword in text for keyword in high_keywords):
            self.priority = 'high'
    
    def check_trigger_rules(self):
        """Check if ticket matches any trigger rules"""
        text = f"{self.subject} {self.description}".lower()
        
        for rule in TriggerRule.objects.filter(is_active=True):
            keywords = rule.get_keyword_list()
            if any(keyword in text for keyword in keywords):
                if rule.action == 'escalate':
                    self.escalate()
                elif rule.action == 'priority_high':
                    self.priority = 'high'
                elif rule.action == 'priority_critical':
                    self.priority = 'critical'
                # Note: Notifications would be handled in a signal or after save
    
    def escalate(self, escalated_by=None):
        """Escalate ticket"""
        if not self.is_escalated:
            self.is_escalated = True
            self.escalated_at = timezone.now()
            self.escalated_by = escalated_by
            if self.priority == 'low':
                self.priority = 'medium'
            elif self.priority == 'medium':
                self.priority = 'high'
            elif self.priority == 'high':
                self.priority = 'critical'
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class TicketHistory(models.Model):
    """Audit trail for all ticket actions"""
    
    ACTION_TYPES = [
        ('created', 'Ticket Created'),
        ('updated', 'Ticket Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('reassigned', 'Reassigned'),
        ('priority_changed', 'Priority Changed'),
        ('escalated', 'Escalated'),
        ('comment_added', 'Comment Added'),
        ('file_attached', 'File Attached'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Ticket Histories"
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.get_action_type_display()}"


class TicketComment(models.Model):
    """Comments on tickets"""
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal comments only visible to agents/admins")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.author.username}"


class TicketAttachment(models.Model):
    """File attachments for tickets including RCA documents"""
    
    ATTACHMENT_TYPES = [
        ('general', 'General Document'),
        ('rca', 'Root Cause Analysis'),
        ('screenshot', 'Screenshot'),
        ('log', 'Log File'),
        ('report', 'Report'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='ticket_attachments/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 
            'xlsx', 'xls', 'csv', 'log', 'zip', 'rar'
        ])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='general')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.file_name} - {self.ticket.ticket_number}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class Notification(models.Model):
    """System notifications for users"""
    
    NOTIFICATION_TYPES = [
        ('ticket_assigned', 'Ticket Assigned'),
        ('ticket_updated', 'Ticket Updated'),
        ('ticket_escalated', 'Ticket Escalated'),
        ('new_comment', 'New Comment'),
        ('status_changed', 'Status Changed'),
        ('trigger_activated', 'Trigger Rule Activated'),
    ]
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
