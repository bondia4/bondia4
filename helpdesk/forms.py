from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Ticket, TicketCategory, TicketComment, TicketAttachment, 
    TriggerRule, CustomUser
)

User = get_user_model()


class TicketForm(forms.ModelForm):
    """Form for creating new tickets"""
    
    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'category', 'severity']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed description of the issue...'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = TicketCategory.objects.all()
        self.fields['category'].empty_label = "Select a category"


class TicketUpdateForm(forms.ModelForm):
    """Form for updating tickets (agents/admins only)"""
    
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'severity', 'assigned_to', 'category']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show agents and admins for assignment
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['agent', 'admin']
        ).order_by('first_name', 'last_name', 'username')
        self.fields['assigned_to'].empty_label = "Unassigned"
        
        self.fields['category'].queryset = TicketCategory.objects.all()


class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to tickets"""
    
    class Meta:
        model = TicketComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add your comment...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hide internal comment option for clients
        if user and user.role == 'client':
            del self.fields['is_internal']


class TicketAttachmentForm(forms.ModelForm):
    """Form for uploading file attachments"""
    
    class Meta:
        model = TicketAttachment
        fields = ['file', 'attachment_type', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.xlsx,.xls,.csv,.log,.zip,.rar'
            }),
            'attachment_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional description of the file...'
            }),
        }


class TriggerRuleForm(forms.ModelForm):
    """Form for creating/editing trigger rules"""
    
    class Meta:
        model = TriggerRule
        fields = ['name', 'keywords', 'action', 'category', 'notify_users', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rule name (e.g., "Security Breach Alert")'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comma-separated keywords (e.g., "urgent, critical, outage, security breach")'
            }),
            'action': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'notify_users': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "All categories"
        self.fields['notify_users'].queryset = User.objects.filter(
            role__in=['agent', 'admin']
        ).order_by('first_name', 'last_name', 'username')


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration"""
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 
                 'phone_number', 'department', 'company']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class TicketSearchForm(forms.Form):
    """Form for searching and filtering tickets"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tickets...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Ticket.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Ticket.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned = forms.ChoiceField(
        choices=[
            ('', 'All Tickets'),
            ('me', 'Assigned to Me'),
            ('unassigned', 'Unassigned'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class TicketCategoryForm(forms.ModelForm):
    """Form for creating/editing ticket categories"""
    
    class Meta:
        model = TicketCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name (e.g., "Technical Support")'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description...'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }


class BulkTicketActionForm(forms.Form):
    """Form for performing bulk actions on tickets"""
    
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('assign', 'Assign to Agent'),
        ('change_status', 'Change Status'),
        ('change_priority', 'Change Priority'),
        ('add_to_category', 'Change Category'),
        ('escalate', 'Escalate'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Optional fields based on action
    agent = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['agent', 'admin']),
        required=False,
        empty_label="Select Agent",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=Ticket.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.all(),
        required=False,
        empty_label="Select Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional comment for this action...'
        })
    )