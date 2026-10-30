from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Organization, Workspace, WorkspaceMembership
from projects.models import Project
from documents.models import Document

User = get_user_model()

class DocumentUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password123', email='tester@test.com', role='director')
        self.org = Organization.objects.create(name='Test Org')
        self.workspace = Workspace.objects.create(name='Test Workspace', organization=self.org)
        
        # Associate user with workspace
        WorkspaceMembership.objects.create(user=self.user, workspace=self.workspace, role='owner')
        
        self.project_a = Project.objects.create(title='Project A', workspace=self.workspace, manager=self.user)
        
        # Setup another workspace and project for isolation testing
        self.other_workspace = Workspace.objects.create(name='Other Workspace', organization=self.org)
        self.project_b = Project.objects.create(title='Project B', workspace=self.other_workspace, manager=self.user)
        
        self.client.login(username='tester', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace.id
        session.save()

    def test_file_list_get_contains_form_with_filtered_projects(self):
        response = self.client.get(reverse('file_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        
        # Queryset must only contain project_a (from active workspace)
        project_ids = list(form.fields['project'].queryset.values_list('id', flat=True))
        self.assertIn(self.project_a.id, project_ids)
        self.assertNotIn(self.project_b.id, project_ids)

    def test_successful_file_upload(self):
        test_file = SimpleUploadedFile("test_spec.pdf", b"pdf content", content_type="application/pdf")
        
        response = self.client.post(reverse('file_list'), {
            'title': 'Design Spec',
            'project': self.project_a.id,
            'file': test_file
        })
        self.assertRedirects(response, reverse('file_list'))
        
        # Verify document is created in db
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.title, 'Design Spec')
        self.assertEqual(doc.project, self.project_a)
        self.assertEqual(doc.uploaded_by, self.user)
        self.assertIn('test_spec', doc.file.name)
        self.assertTrue(doc.file.name.endswith('.pdf'))

    def test_failed_file_upload_validation(self):
        # Post invalid data (missing title and file)
        response = self.client.post(reverse('file_list'), {
            'project': self.project_a.id,
        })
        
        # Response should be 200 (re-render form on validation failure)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['show_modal'])
        
        # Check form validation errors
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('title', form.errors)
        self.assertIn('file', form.errors)
