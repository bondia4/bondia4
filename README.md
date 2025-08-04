# Blue River Technology Solutions - Helpdesk System

A comprehensive Django-based helpdesk system designed for efficient ticket management, automated prioritization, and real-time client visibility.

## 🚀 Features

### Core Functionality

1. **Central Ticketing Hub**
   - Client portal for ticket submission
   - Comprehensive ticket fields (subject, description, category, severity, priority, status)
   - Automatic ticket numbering (BRTS-YYYY-NNNN format)
   - Categories: Technical Support, Security, General Complaint, Feature Request, Account Issues

2. **Auto-Prioritization System**
   - Intelligent keyword analysis for automatic priority assignment
   - Keywords like "urgent", "critical", "outage", "security breach" trigger priority escalation
   - Manual priority override capability for agents/admins

3. **Comprehensive Audit Trail**
   - Complete history tracking for all ticket actions
   - Tracks status changes, assignments, comments, file uploads, escalations
   - Timestamped entries with actor identification

4. **Client Dashboard & Visibility**
   - Real-time status updates for clients
   - Assigned agent visibility
   - Activity timeline and notifications
   - File attachment support

5. **Advanced Trigger Rules**
   - Configurable keyword-based auto-escalation
   - Automated notifications to specific team members
   - Email alerts for critical issues
   - Customizable rule management

6. **File Management System**
   - RCA (Root Cause Analysis) document uploads
   - Screenshot and log file support
   - Multiple file format support
   - Drag-and-drop interface

7. **Analytics Dashboard**
   - Daily, weekly, and monthly ticket trends
   - Resolution time analytics
   - Agent performance metrics
   - Interactive charts and graphs

## 🛠 Technology Stack

- **Backend**: Django 5.2.4
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5.1.3, JavaScript ES6
- **Charts**: Chart.js
- **Icons**: Bootstrap Icons
- **Authentication**: Django built-in auth with custom user model

## 📋 System Requirements

- Python 3.8+
- Django 5.2+
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd workspace

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django

# Run migrations
python manage.py migrate

# Create sample data
python setup_sample_data.py

# Start development server
python manage.py runserver
```

### 2. Access the System

- **Main Application**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/

### 3. Test Accounts

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| Admin | admin | admin123 | System administrator |
| Client | john_client | client123 | Sample client user |
| Client | jane_client | client123 | Sample client user |
| Agent | mike_agent | agent123 | Support agent |
| Agent | sarah_agent | agent123 | Support agent |

## 📁 Project Structure

```
workspace/
├── helpdesk/                   # Main helpdesk application
│   ├── models.py              # Database models
│   ├── views.py               # View logic
│   ├── forms.py               # Django forms
│   ├── admin.py               # Admin interface
│   ├── signals.py             # Event handlers
│   └── urls.py                # URL routing
├── helpdesk_system/           # Django project settings
├── templates/                 # HTML templates
│   └── helpdesk/
├── static/                    # Static files (CSS, JS)
│   ├── css/
│   ├── js/
│   └── img/
├── media/                     # User uploads
├── manage.py                  # Django management script
└── setup_sample_data.py       # Sample data generator
```

## 🎯 User Roles & Permissions

### Client
- Create tickets
- View own tickets
- Add comments and attachments
- Track ticket status
- Receive notifications

### Support Agent
- View all tickets
- Update ticket status and priority
- Assign tickets
- Add internal/external comments
- Upload RCA documents
- Escalate tickets

### Administrator
- All agent permissions
- Manage trigger rules
- Access analytics dashboard
- User management
- System configuration

## 🔧 Key Models

### CustomUser
Extended Django user model with roles (client, agent, admin) and additional fields for company information.

### Ticket
Core ticket model with auto-generated numbers, priority/status tracking, and relationship management.

### TicketHistory
Audit trail model tracking all ticket changes with timestamps and actors.

### TriggerRule
Configurable rules for automatic escalation and notifications based on keywords.

### TicketAttachment
File upload system supporting various document types including RCA reports.

## 🚨 Auto-Prioritization Keywords

### Critical Priority
- "critical", "emergency", "outage", "down", "breach", "security breach", "data loss"

### High Priority
- "urgent", "high", "important", "asap", "immediate", "production"

## 📊 Analytics Features

- **Ticket Volume**: Daily, weekly, monthly trends
- **Resolution Time**: Average time to resolve tickets
- **Status Distribution**: Open vs resolved ticket ratios
- **Category Analysis**: Tickets by support category
- **Agent Performance**: Individual agent metrics
- **Priority Trends**: Critical vs normal priority distribution

## 🔔 Notification System

- Real-time notification dropdown
- Email notifications (configurable)
- Auto-refresh every 30 seconds
- Trigger-based alerts
- Assignment notifications

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-friendly interface
- **Dark Mode Support**: System preference detection
- **Real-time Updates**: Live notification system
- **Drag & Drop**: File upload interface
- **Interactive Charts**: Chart.js powered analytics
- **Modern Styling**: Bootstrap 5 with custom themes

## 🔧 Configuration

### Email Settings (Production)
Update `helpdesk_system/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'Blue River Technology Solutions <noreply@example.com>'
```

### Database (Production)
For PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'helpdesk_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False`
2. Configure proper `ALLOWED_HOSTS`
3. Set up PostgreSQL database
4. Configure email settings
5. Set up static file serving
6. Enable HTTPS (SSL certificates)
7. Configure backup system

### Static Files
```bash
python manage.py collectstatic
```

## 🧪 Testing Sample Scenarios

1. **Create a Critical Ticket**
   - Login as john_client
   - Create ticket with "Critical server outage" 
   - Observe auto-prioritization and escalation

2. **Agent Workflow**
   - Login as mike_agent
   - View assigned tickets
   - Update status and add comments
   - Upload RCA document

3. **Admin Analytics**
   - Login as admin
   - Access analytics dashboard
   - Configure trigger rules
   - Monitor system performance

## 📝 Customization

### Adding New Categories
1. Access admin panel
2. Navigate to Ticket Categories
3. Add new category with color coding

### Custom Trigger Rules
1. Admin panel → Trigger Rules
2. Define keywords and actions
3. Set notification recipients

### Styling Customization
- Edit `static/css/helpdesk.css`
- Modify Bootstrap variables
- Update color schemes

## 🐛 Troubleshooting

### Common Issues

1. **Static files not loading**
   ```bash
   python manage.py collectstatic
   ```

2. **Database errors**
   ```bash
   python manage.py migrate
   ```

3. **Permission errors**
   - Check user roles in admin panel
   - Verify authentication

## 📞 Support

For technical support or questions about this helpdesk system:
- Email: admin@brts.com
- Create a ticket in the system
- Check the admin panel for system logs

## 📄 License

This project is proprietary software developed for Blue River Technology Solutions.

---

**Blue River Technology Solutions** - Professional IT Support & Services