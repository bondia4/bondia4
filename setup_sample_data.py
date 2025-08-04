#!/usr/bin/env python
"""
Setup script for BRTS Helpdesk sample data
Run this after migrations to populate the database with sample data.
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpdesk_system.settings')
django.setup()

from helpdesk.models import (
    TicketCategory, TriggerRule, Ticket, TicketComment, 
    TicketAttachment, Notification
)

User = get_user_model()

def create_sample_data():
    print("Setting up sample data for BRTS Helpdesk...")
    
    # Set superuser password
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.role = 'admin'
        admin.first_name = 'System'
        admin.last_name = 'Administrator'
        admin.save()
        print("✓ Updated admin user password to 'admin123'")
    except User.DoesNotExist:
        print("Creating admin user...")
        admin = User.objects.create_user(
            username='admin',
            email='admin@brts.com',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        print("✓ Created admin user with password 'admin123'")
    
    # Create sample users
    users_data = [
        {
            'username': 'john_client',
            'email': 'john@example.com',
            'password': 'client123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'client',
            'company': 'Acme Corporation',
            'department': 'IT'
        },
        {
            'username': 'jane_client',
            'email': 'jane@example.com',
            'password': 'client123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'client',
            'company': 'Tech Solutions Inc',
            'department': 'Finance'
        },
        {
            'username': 'mike_agent',
            'email': 'mike@brts.com',
            'password': 'agent123',
            'first_name': 'Mike',
            'last_name': 'Johnson',
            'role': 'agent',
            'department': 'Technical Support'
        },
        {
            'username': 'sarah_agent',
            'email': 'sarah@brts.com',
            'password': 'agent123',
            'first_name': 'Sarah',
            'last_name': 'Wilson',
            'role': 'agent',
            'department': 'Technical Support'
        }
    ]
    
    created_users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"✓ Created user: {user.username} ({user.get_role_display()})")
        created_users[user.username] = user
    
    # Create ticket categories
    categories_data = [
        {
            'name': 'Technical Support',
            'description': 'Hardware and software technical issues',
            'color': '#007bff'
        },
        {
            'name': 'Security',
            'description': 'Security-related issues and breaches',
            'color': '#dc3545'
        },
        {
            'name': 'General Complaint',
            'description': 'General complaints and feedback',
            'color': '#fd7e14'
        },
        {
            'name': 'Feature Request',
            'description': 'New feature requests and enhancements',
            'color': '#28a745'
        },
        {
            'name': 'Account Issues',
            'description': 'User account and access issues',
            'color': '#6f42c1'
        }
    ]
    
    created_categories = {}
    for cat_data in categories_data:
        category, created = TicketCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"✓ Created category: {category.name}")
        created_categories[category.name] = category
    
    # Create trigger rules
    trigger_rules_data = [
        {
            'name': 'Security Breach Alert',
            'keywords': 'security breach, hack, compromised, malware, virus',
            'action': 'priority_critical',
            'category': created_categories['Security'],
            'is_active': True
        },
        {
            'name': 'System Outage Alert',
            'keywords': 'outage, down, offline, crash, critical',
            'action': 'escalate',
            'category': None,
            'is_active': True
        },
        {
            'name': 'Urgent Priority',
            'keywords': 'urgent, asap, immediate, emergency',
            'action': 'priority_high',
            'category': None,
            'is_active': True
        },
        {
            'name': 'Security Team Notification',
            'keywords': 'security, breach, unauthorized access',
            'action': 'notify',
            'category': created_categories['Security'],
            'is_active': True
        }
    ]
    
    for rule_data in trigger_rules_data:
        rule, created = TriggerRule.objects.get_or_create(
            name=rule_data['name'],
            defaults=rule_data
        )
        if created:
            print(f"✓ Created trigger rule: {rule.name}")
            # Add notification users for security team notification
            if rule.action == 'notify':
                rule.notify_users.add(admin)
                for username in ['mike_agent', 'sarah_agent']:
                    if username in created_users:
                        rule.notify_users.add(created_users[username])
    
    # Create sample tickets
    tickets_data = [
        {
            'subject': 'Email server is down - critical outage',
            'description': 'Our email server has been down for 2 hours. This is affecting all company communications. Please help urgently!',
            'category': created_categories['Technical Support'],
            'severity': 'critical',
            'created_by': created_users['john_client'],
            'assigned_to': created_users['mike_agent'],
            'status': 'in_progress'
        },
        {
            'subject': 'Cannot access my account',
            'description': 'I am unable to log into my company account. I keep getting an "invalid credentials" error even though I am sure my password is correct.',
            'category': created_categories['Account Issues'],
            'severity': 'high',
            'created_by': created_users['jane_client'],
            'assigned_to': created_users['sarah_agent'],
            'status': 'open'
        },
        {
            'subject': 'Request for mobile app feature',
            'description': 'It would be great if we could have push notifications in the mobile app. This would help us stay updated on important announcements.',
            'category': created_categories['Feature Request'],
            'severity': 'low',
            'created_by': created_users['john_client'],
            'status': 'open'
        },
        {
            'subject': 'Possible security breach detected',
            'description': 'I noticed some unusual activity on my account. There were login attempts from unknown IP addresses. Please investigate this security issue immediately.',
            'category': created_categories['Security'],
            'severity': 'critical',
            'created_by': created_users['jane_client'],
            'assigned_to': created_users['mike_agent'],
            'status': 'open'
        },
        {
            'subject': 'Printer not working in office',
            'description': 'The main printer in our office has stopped working. It shows an error message "Paper jam" but there is no paper jam. Can someone help?',
            'category': created_categories['Technical Support'],
            'severity': 'medium',
            'created_by': created_users['john_client'],
            'status': 'resolved'
        }
    ]
    
    for i, ticket_data in enumerate(tickets_data):
        ticket, created = Ticket.objects.get_or_create(
            subject=ticket_data['subject'],
            defaults=ticket_data
        )
        if created:
            print(f"✓ Created ticket: {ticket.ticket_number} - {ticket.subject[:50]}...")
            
            # Add some comments to tickets
            if i == 0:  # Email server ticket
                TicketComment.objects.create(
                    ticket=ticket,
                    author=created_users['mike_agent'],
                    content="I'm investigating the issue. It appears to be a server hardware problem. ETA for resolution: 2 hours.",
                    is_internal=False
                )
                TicketComment.objects.create(
                    ticket=ticket,
                    author=created_users['john_client'],
                    content="Thank you for the update. Please keep me posted on the progress.",
                    is_internal=False
                )
            elif i == 1:  # Account access ticket
                TicketComment.objects.create(
                    ticket=ticket,
                    author=created_users['sarah_agent'],
                    content="I've reset your password. Please check your email for the new temporary password.",
                    is_internal=False
                )
    
    print(f"\n🎉 Sample data setup complete!")
    print(f"")
    print(f"Login credentials:")
    print(f"  Admin: admin / admin123")
    print(f"  Client 1: john_client / client123")
    print(f"  Client 2: jane_client / client123") 
    print(f"  Agent 1: mike_agent / agent123")
    print(f"  Agent 2: sarah_agent / agent123")
    print(f"")
    print(f"Access the system at: http://localhost:8000/")
    print(f"Admin panel at: http://localhost:8000/admin/")

if __name__ == '__main__':
    create_sample_data()