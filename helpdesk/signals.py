from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Ticket, TicketHistory, TicketComment, TicketAttachment, Notification, TriggerRule

User = get_user_model()


@receiver(pre_save, sender=Ticket)
def ticket_pre_save(sender, instance, **kwargs):
    """Store original values before save for comparison"""
    if instance.pk:
        try:
            instance._original = Ticket.objects.get(pk=instance.pk)
        except Ticket.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """Handle ticket creation and updates"""
    
    if created:
        # Log ticket creation
        TicketHistory.objects.create(
            ticket=instance,
            action_type='created',
            actor=instance.created_by,
            description=f"Ticket created with subject: {instance.subject}",
            new_value=f"Status: {instance.status}, Priority: {instance.priority}"
        )
        
        # Check for trigger rules that send notifications
        check_trigger_notifications(instance)
        
        # Auto-assign to available agent if category has default assignment rules
        auto_assign_ticket(instance)
        
    else:
        # Log changes for existing tickets
        original = getattr(instance, '_original', None)
        if original:
            log_ticket_changes(instance, original)


def log_ticket_changes(instance, original):
    """Log specific changes to ticket"""
    changes = []
    
    # Status change
    if instance.status != original.status:
        TicketHistory.objects.create(
            ticket=instance,
            action_type='status_changed',
            actor=None,  # Will be set by view
            description=f"Status changed from {original.get_status_display()} to {instance.get_status_display()}",
            old_value=original.status,
            new_value=instance.status
        )
        
        # Send notification to client
        if instance.created_by:
            Notification.objects.create(
                recipient=instance.created_by,
                notification_type='status_changed',
                title=f"Ticket {instance.ticket_number} Status Updated",
                message=f"Your ticket status has been changed from {original.get_status_display()} to {instance.get_status_display()}",
                ticket=instance
            )
    
    # Assignment change
    if instance.assigned_to != original.assigned_to:
        if instance.assigned_to:
            action_type = 'reassigned' if original.assigned_to else 'assigned'
            description = f"Ticket assigned to {instance.assigned_to.get_full_name() or instance.assigned_to.username}"
            
            TicketHistory.objects.create(
                ticket=instance,
                action_type=action_type,
                actor=None,  # Will be set by view
                description=description,
                old_value=str(original.assigned_to) if original.assigned_to else None,
                new_value=str(instance.assigned_to)
            )
            
            # Notify assigned agent
            Notification.objects.create(
                recipient=instance.assigned_to,
                notification_type='ticket_assigned',
                title=f"New Ticket Assigned: {instance.ticket_number}",
                message=f"You have been assigned ticket: {instance.subject}",
                ticket=instance
            )
    
    # Priority change
    if instance.priority != original.priority:
        TicketHistory.objects.create(
            ticket=instance,
            action_type='priority_changed',
            actor=None,  # Will be set by view
            description=f"Priority changed from {original.get_priority_display()} to {instance.get_priority_display()}",
            old_value=original.priority,
            new_value=instance.priority
        )
    
    # Escalation
    if instance.is_escalated and not original.is_escalated:
        TicketHistory.objects.create(
            ticket=instance,
            action_type='escalated',
            actor=instance.escalated_by,
            description=f"Ticket escalated by {instance.escalated_by.get_full_name() if instance.escalated_by else 'System'}",
            new_value=f"Priority: {instance.priority}"
        )
        
        # Notify escalation to admins
        admins = User.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='ticket_escalated',
                title=f"Ticket Escalated: {instance.ticket_number}",
                message=f"Ticket has been escalated with priority: {instance.get_priority_display()}",
                ticket=instance
            )


def check_trigger_notifications(instance):
    """Check trigger rules and send notifications"""
    text = f"{instance.subject} {instance.description}".lower()
    
    for rule in TriggerRule.objects.filter(is_active=True, action='notify'):
        keywords = rule.get_keyword_list()
        if any(keyword in text for keyword in keywords):
            # Send notifications to specified users
            for user in rule.notify_users.all():
                Notification.objects.create(
                    recipient=user,
                    notification_type='trigger_activated',
                    title=f"Trigger Alert: {rule.name}",
                    message=f"Ticket {instance.ticket_number} matches trigger rule '{rule.name}'. Keywords detected: {', '.join(keywords)}",
                    ticket=instance
                )


def auto_assign_ticket(instance):
    """Auto-assign ticket to available agent based on category or workload"""
    if not instance.assigned_to and instance.category:
        # Find agent with least assigned open tickets
        agents = User.objects.filter(role='agent')
        if agents.exists():
            # Get agent with minimum workload
            min_tickets = float('inf')
            best_agent = None
            
            for agent in agents:
                open_tickets = agent.assigned_tickets.filter(status__in=['open', 'in_progress']).count()
                if open_tickets < min_tickets:
                    min_tickets = open_tickets
                    best_agent = agent
            
            if best_agent:
                instance.assigned_to = best_agent
                instance.save(update_fields=['assigned_to'])


@receiver(post_save, sender=TicketComment)
def comment_post_save(sender, instance, created, **kwargs):
    """Handle comment creation"""
    if created:
        # Log comment addition
        TicketHistory.objects.create(
            ticket=instance.ticket,
            action_type='comment_added',
            actor=instance.author,
            description=f"Comment added by {instance.author.get_full_name() or instance.author.username}",
            new_value=instance.content[:100] + "..." if len(instance.content) > 100 else instance.content
        )
        
        # Notify relevant users (exclude comment author)
        users_to_notify = []
        
        # Always notify ticket creator if they're not the comment author
        if instance.ticket.created_by != instance.author:
            users_to_notify.append(instance.ticket.created_by)
        
        # Notify assigned agent if they're not the comment author
        if instance.ticket.assigned_to and instance.ticket.assigned_to != instance.author:
            users_to_notify.append(instance.ticket.assigned_to)
        
        # Don't notify on internal comments to clients
        if instance.is_internal:
            users_to_notify = [user for user in users_to_notify if not user.is_client]
        
        for user in users_to_notify:
            Notification.objects.create(
                recipient=user,
                notification_type='new_comment',
                title=f"New Comment on Ticket {instance.ticket.ticket_number}",
                message=f"New comment by {instance.author.get_full_name() or instance.author.username}",
                ticket=instance.ticket
            )


@receiver(post_save, sender=TicketAttachment)
def attachment_post_save(sender, instance, created, **kwargs):
    """Handle file attachment"""
    if created:
        # Log file attachment
        TicketHistory.objects.create(
            ticket=instance.ticket,
            action_type='file_attached',
            actor=instance.uploaded_by,
            description=f"File attached: {instance.file_name} ({instance.attachment_type})",
            new_value=f"File: {instance.file_name}, Size: {instance.file_size_mb}MB"
        )
        
        # Notify relevant users about file attachment
        users_to_notify = []
        
        # Notify ticket creator if they're not the uploader
        if instance.ticket.created_by != instance.uploaded_by:
            users_to_notify.append(instance.ticket.created_by)
        
        # Notify assigned agent if they're not the uploader
        if instance.ticket.assigned_to and instance.ticket.assigned_to != instance.uploaded_by:
            users_to_notify.append(instance.ticket.assigned_to)
        
        for user in users_to_notify:
            Notification.objects.create(
                recipient=user,
                notification_type='ticket_updated',
                title=f"File Attached to Ticket {instance.ticket.ticket_number}",
                message=f"New {instance.get_attachment_type_display().lower()} attached: {instance.file_name}",
                ticket=instance.ticket
            )