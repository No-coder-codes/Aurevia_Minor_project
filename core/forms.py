from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Workspace, Organization

class HierarchicalUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, 
                                help_text="Leave blank to use suggested: NexusFlow@2026")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.role == 'project_manager':
                self.fields['role'].choices = [('team_member', 'Team Member')]
                self.fields['role'].initial = 'team_member'
            elif user.role == 'director':
                self.fields['role'].choices = [
                    ('project_manager', 'Project Manager'),
                    ('team_member', 'Team Member')
                ]

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if not password:
            password = "NexusFlow@2026"
        user.set_password(password)
        if commit:
            user.save()
        return user

from projects.models import Project
from tasks.models import Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'members']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Academic Complex IT Modernization'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe project scope, institutional objectives, and milestones...'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'assignee', 'status', 'priority', 'due_date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Details and action items...'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['name']


from documents.models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'project', 'file']

    def __init__(self, *args, **kwargs):
        workspace = kwargs.pop('workspace', None)
        super().__init__(*args, **kwargs)
        self.fields['project'].empty_label = "Choose..."
        if workspace:
            self.fields['project'].queryset = Project.objects.filter(workspace=workspace)
        else:
            self.fields['project'].queryset = Project.objects.none()
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['project'].widget.attrs.update({'class': 'form-select'})
