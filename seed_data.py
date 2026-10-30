import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'management_system.settings')
django.setup()

from core.models import User
from projects.models import Project

def seed():
    # Create Director
    if not User.objects.filter(username='director').exists():
        User.objects.create_superuser('director', 'director@example.com', 'admin123', role='director')
        print("Created Director: director/admin123")

    # Create Project Manager
    if not User.objects.filter(username='pm1').exists():
        User.objects.create_user('pm1', 'pm1@example.com', 'pm123', role='project_manager')
        print("Created Manager: pm1/pm123")

    # Create Sample Project
    director = User.objects.get(username='director')
    if not Project.objects.filter(title='Sample Project').exists():
        Project.objects.create(title='Sample Project', manager=director, status='active')
        print("Created Sample Project")

if __name__ == '__main__':
    seed()
