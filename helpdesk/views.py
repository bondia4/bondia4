from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta, datetime
import json

from .models import (
    Ticket, TicketCategory, TicketComment, TicketAttachment, 
    TicketHistory, Notification, TriggerRule
)
from .forms import (
    TicketForm, TicketCommentForm, TicketAttachmentForm, 
    TicketUpdateForm, TriggerRuleForm
)

User = get_user_model()


def is_client(user):
    """Check if user is a client"""
    return user.is_authenticated and user.role == 'client'

def is_agent_or_admin(user):
    """Check if user is an agent or admin"""
    return user.is_authenticated and user.role in ['agent', 'admin']

def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and user.role == 'admin'


@login_required
def dashboard(request):
    """Main dashboard - redirects based on user role"""
    if request.user.is_client:
        return redirect('helpdesk:client_dashboard')
    elif request.user.is_agent or request.user.is_admin:
        return redirect('helpdesk:agent_dashboard')
    else:
        return redirect('helpdesk:client_dashboard')


@login_required
@user_passes_test(is_client)
def client_dashboard(request):
    """Client dashboard showing their tickets and status"""
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get counts by status
    status_counts = tickets.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    # Recent activity (last 10 items)
    recent_history = TicketHistory.objects.filter(
        ticket__created_by=request.user
    ).order_by('-timestamp')[:10]
    
    # Unread notifications
    notifications = request.user.notifications.filter(is_read=False)[:5]
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'status_counts': status_dict,
        'recent_history': recent_history,
        'notifications': notifications,
        'total_tickets': tickets.count(),
    }
    return render(request, 'helpdesk/client_dashboard.html', context)


@login_required
@user_passes_test(is_agent_or_admin)
def agent_dashboard(request):
    """Agent/Admin dashboard with ticket overview and analytics"""
    
    # Get tickets based on role
    if request.user.is_admin:
        tickets = Ticket.objects.all()
        assigned_tickets = Ticket.objects.filter(assigned_to=request.user)
    else:
        tickets = Ticket.objects.all()  # Agents can see all tickets
        assigned_tickets = Ticket.objects.filter(assigned_to=request.user)
    
    # Statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status='open').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'pending_tickets': tickets.filter(status='pending').count(),
        'resolved_today': tickets.filter(status='resolved', resolved_at__date=today).count(),
        'assigned_to_me': assigned_tickets.count(),
        'critical_tickets': tickets.filter(priority='critical', status__in=['open', 'in_progress']).count(),
        'escalated_tickets': tickets.filter(is_escalated=True, status__in=['open', 'in_progress']).count(),
    }
    
    # Recent tickets
    recent_tickets = tickets.order_by('-created_at')[:10]
    
    # My assigned tickets
    my_tickets = assigned_tickets.filter(
        status__in=['open', 'in_progress', 'pending']
    ).order_by('-priority', '-created_at')[:10]
    
    # Unread notifications
    notifications = request.user.notifications.filter(is_read=False)[:5]
    
    context = {
        'stats': stats,
        'recent_tickets': recent_tickets,
        'my_tickets': my_tickets,
        'notifications': notifications,
    }
    return render(request, 'helpdesk/agent_dashboard.html', context)


@login_required
def create_ticket(request):
    """Create new ticket"""
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, f'Ticket {ticket.ticket_number} created successfully!')
            return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketForm()
    
    return render(request, 'helpdesk/create_ticket.html', {'form': form})


@login_required
def ticket_detail(request, ticket_id):
    """Detailed ticket view with comments and history"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check permissions
    if request.user.is_client and ticket.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to view this ticket.")
    
    # Get comments (filter internal comments for clients)
    comments = ticket.comments.all()
    if request.user.is_client:
        comments = comments.filter(is_internal=False)
    
    # Get attachments
    attachments = ticket.attachments.all()
    
    # Get history
    history = ticket.history.all()[:20]  # Last 20 history items
    
    # Forms
    comment_form = TicketCommentForm()
    attachment_form = TicketAttachmentForm()
    
    # Update form for agents/admins
    update_form = None
    if request.user.is_agent or request.user.is_admin:
        update_form = TicketUpdateForm(instance=ticket)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': attachments,
        'history': history,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
        'update_form': update_form,
    }
    return render(request, 'helpdesk/ticket_detail.html', context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, ticket_id):
    """Add comment to ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check permissions
    if request.user.is_client and ticket.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to comment on this ticket.")
    
    form = TicketCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        # Only agents/admins can create internal comments
        if request.user.is_client:
            comment.is_internal = False
        comment.save()
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Error adding comment.')
    
    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)


@login_required
@require_http_methods(["POST"])
def upload_attachment(request, ticket_id):
    """Upload attachment to ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check permissions
    if request.user.is_client and ticket.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to upload files to this ticket.")
    
    form = TicketAttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.ticket = ticket
        attachment.uploaded_by = request.user
        attachment.save()
        messages.success(request, 'File uploaded successfully!')
    else:
        messages.error(request, 'Error uploading file.')
    
    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)


@login_required
@user_passes_test(is_agent_or_admin)
@require_http_methods(["POST"])
def update_ticket(request, ticket_id):
    """Update ticket (agents/admins only)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    form = TicketUpdateForm(request.POST, instance=ticket)
    
    if form.is_valid():
        # Store original values for history
        original = Ticket.objects.get(id=ticket.id)
        updated_ticket = form.save()
        
        # Log the update
        TicketHistory.objects.create(
            ticket=updated_ticket,
            action_type='updated',
            actor=request.user,
            description=f"Ticket updated by {request.user.get_full_name() or request.user.username}",
        )
        
        messages.success(request, 'Ticket updated successfully!')
    else:
        messages.error(request, 'Error updating ticket.')
    
    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)


@login_required
@user_passes_test(is_agent_or_admin)
def ticket_list(request):
    """List all tickets with filtering and search"""
    tickets = Ticket.objects.all().select_related('created_by', 'assigned_to', 'category')
    
    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    category_filter = request.GET.get('category')
    assigned_filter = request.GET.get('assigned')
    search = request.GET.get('search')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if category_filter:
        tickets = tickets.filter(category_id=category_filter)
    if assigned_filter:
        if assigned_filter == 'me':
            tickets = tickets.filter(assigned_to=request.user)
        elif assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
    if search:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(description__icontains=search) |
            Q(created_by__username__icontains=search)
        )
    
    # Ordering
    tickets = tickets.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    categories = TicketCategory.objects.all()
    agents = User.objects.filter(role__in=['agent', 'admin'])
    
    context = {
        'tickets': page_obj,
        'categories': categories,
        'agents': agents,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'category': category_filter,
            'assigned': assigned_filter,
            'search': search,
        }
    }
    return render(request, 'helpdesk/ticket_list.html', context)


@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Analytics dashboard for admins"""
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Basic statistics
    total_tickets = Ticket.objects.count()
    tickets_in_range = Ticket.objects.filter(created_at__date__range=[start_date, end_date])
    
    stats = {
        'total_tickets': total_tickets,
        'tickets_in_range': tickets_in_range.count(),
        'resolved_in_range': tickets_in_range.filter(status='resolved').count(),
        'avg_resolution_time': calculate_avg_resolution_time(tickets_in_range),
        'escalated_tickets': tickets_in_range.filter(is_escalated=True).count(),
    }
    
    # Tickets by status
    status_data = tickets_in_range.values('status').annotate(count=Count('id'))
    
    # Tickets by priority
    priority_data = tickets_in_range.values('priority').annotate(count=Count('id'))
    
    # Tickets by category
    category_data = tickets_in_range.values('category__name').annotate(count=Count('id'))
    
    # Daily ticket creation (last 30 days)
    daily_data = []
    for i in range(30):
        date = end_date - timedelta(days=i)
        count = Ticket.objects.filter(created_at__date=date).count()
        daily_data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    daily_data.reverse()
    
    # Agent performance
    agent_data = User.objects.filter(role='agent').annotate(
        assigned_count=Count('assigned_tickets'),
        resolved_count=Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved'))
    )
    
    context = {
        'stats': stats,
        'status_data': list(status_data),
        'priority_data': list(priority_data),
        'category_data': list(category_data),
        'daily_data': daily_data,
        'agent_data': agent_data,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'helpdesk/analytics_dashboard.html', context)


def calculate_avg_resolution_time(tickets):
    """Calculate average resolution time in hours"""
    resolved_tickets = tickets.filter(status='resolved', resolved_at__isnull=False)
    if not resolved_tickets.exists():
        return 0
    
    total_time = timedelta()
    count = 0
    
    for ticket in resolved_tickets:
        if ticket.resolved_at and ticket.created_at:
            total_time += ticket.resolved_at - ticket.created_at
            count += 1
    
    if count == 0:
        return 0
    
    avg_time = total_time / count
    return round(avg_time.total_seconds() / 3600, 2)  # Convert to hours


@login_required
@user_passes_test(is_admin)
def trigger_rules_management(request):
    """Manage trigger rules"""
    rules = TriggerRule.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = TriggerRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trigger rule created successfully!')
            return redirect('helpdesk:trigger_rules')
    else:
        form = TriggerRuleForm()
    
    context = {
        'rules': rules,
        'form': form,
    }
    return render(request, 'helpdesk/trigger_rules.html', context)


@login_required
def notifications_view(request):
    """View and manage notifications"""
    notifications = request.user.notifications.all().order_by('-created_at')
    
    # Mark as read if requested
    if request.GET.get('mark_read'):
        notification_id = request.GET.get('mark_read')
        try:
            notification = notifications.get(id=notification_id)
            notification.is_read = True
            notification.save()
        except Notification.DoesNotExist:
            pass
    
    # Mark all as read
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
        return redirect('helpdesk:notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'helpdesk/notifications.html', context)


@login_required
def get_notifications_json(request):
    """API endpoint for getting notifications as JSON"""
    notifications = request.user.notifications.filter(is_read=False)[:5]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'ticket_id': n.ticket.id if n.ticket else None,
    } for n in notifications]
    
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
@user_passes_test(is_agent_or_admin)
@require_http_methods(["POST"])
def escalate_ticket(request, ticket_id):
    """Escalate a ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket.escalate(escalated_by=request.user)
    ticket.save()
    
    messages.success(request, f'Ticket {ticket.ticket_number} has been escalated!')
    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)


@login_required
@user_passes_test(is_agent_or_admin)
@require_http_methods(["POST"])
def assign_ticket(request, ticket_id):
    """Assign ticket to agent"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    agent_id = request.POST.get('agent_id')
    
    if agent_id:
        agent = get_object_or_404(User, id=agent_id, role__in=['agent', 'admin'])
        ticket.assigned_to = agent
        ticket.save()
        messages.success(request, f'Ticket assigned to {agent.get_full_name() or agent.username}!')
    else:
        ticket.assigned_to = None
        ticket.save()
        messages.success(request, 'Ticket unassigned!')
    
    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)
