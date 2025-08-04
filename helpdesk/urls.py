from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard, name='dashboard'),
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    
    # Ticket Management URLs
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/update/', views.update_ticket, name='update_ticket'),
    path('tickets/<int:ticket_id>/escalate/', views.escalate_ticket, name='escalate_ticket'),
    path('tickets/<int:ticket_id>/assign/', views.assign_ticket, name='assign_ticket'),
    
    # Comments and Attachments
    path('tickets/<int:ticket_id>/comment/', views.add_comment, name='add_comment'),
    path('tickets/<int:ticket_id>/upload/', views.upload_attachment, name='upload_attachment'),
    
    # Analytics and Reporting
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Trigger Rules Management
    path('triggers/', views.trigger_rules_management, name='trigger_rules'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/', views.get_notifications_json, name='notifications_json'),
]