# SMS Implementation Examples

## Basic Usage Examples

### 1. Send Single SMS

```python
from portal.utils import send_sms

# Simple send
result = send_sms('+919876543210', 'Hello! This is a test message.')

# Check result
if result['success']:
    print(f"Message sent with ID: {result['message_id']}")
else:
    print(f"Error: {result.get('error')}")
```

### 2. Send to Multiple People

```python
from portal.utils import send_sms_bulk

recipients = [
    '+919876543210',
    '+919876543211',
    '+919876543212',
]

results = send_sms_bulk(recipients, 'Bulk message to all!')

print(f"Sent: {len(results['sent'])} messages")
print(f"Failed: {len(results['failed'])} messages")

for failed in results['failed']:
    print(f"Failed to {failed['phone']}: {failed['reason']}")
```

### 3. Format Phone Numbers

```python
from portal.utils import format_phone_e164

# Works with various formats
phone1 = format_phone_e164('9876543210')           # → +919876543210
phone2 = format_phone_e164('+919876543210')        # → +919876543210
phone3 = format_phone_e164('919876543210')         # → +919876543210
phone4 = format_phone_e164('+1234567890')          # → +1234567890
```

### 4. Notify Student Approval

```python
from portal.utils import notify_student_approval
from portal.models import StudentProfile

# In your view
profile = StudentProfile.objects.get(id=1)

try:
    result = notify_student_approval(profile)
    if result['success']:
        messages.success(request, "Student approved and notified!")
    else:
        messages.warning(request, f"Approved but SMS failed: {result['error']}")
except Exception as e:
    messages.warning(request, f"Error: {str(e)}")
```

### 5. Notify Application Update

```python
from portal.utils import notify_application_update
from portal.models import Application

# In your view
app = Application.objects.get(id=1)
app.status = 'Interview Scheduled'
app.save()

try:
    result = notify_application_update(app)
    if result['success']:
        messages.success(request, "Status updated and student notified!")
except Exception as e:
    messages.error(request, f"Failed to notify student: {str(e)}")
```

### 6. Notify New Job Posting

```python
from portal.utils import notify_new_job_posting
from portal.models import JobPosting, StudentProfile
from django.db.models import Q

# Get eligible students for a job
job = JobPosting.objects.get(id=1)
eligible_students = StudentProfile.objects.filter(
    is_approved=True,
    cgpa__gte=job.min_cgpa
)

# Get their phone numbers
student_phones = [student.phone for student in eligible_students]

# Send notification
try:
    results = notify_new_job_posting(job, student_phones)
    print(f"Notified {len(results['sent'])} students")
except Exception as e:
    print(f"Notification failed: {str(e)}")
```

---

## Integration in Views

### Example 1: Student Approval in Admin View

```python
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from portal.models import StudentProfile
from portal.utils import notify_student_approval

@login_required
def approve_student_view(request, student_id):
    """Approve student and send SMS notification."""
    if not request.user.is_staff:
        return redirect('login')
    
    profile = get_object_or_404(StudentProfile, id=student_id)
    
    # Update database
    profile.is_approved = True
    profile.user.is_active = True
    profile.user.save()
    profile.save()
    
    # Send SMS notification
    try:
        result = notify_student_approval(profile)
        if result['success']:
            messages.success(
                request, 
                f"Student approved and SMS sent to {result['to']}"
            )
        else:
            messages.warning(
                request,
                f"Student approved but SMS failed: {result.get('error')}"
            )
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin_dash')
```

### Example 2: Job Application Status Update

```python
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from portal.models import Application
from portal.utils import notify_application_update

@login_required
def update_app_status(request, app_id, status):
    """Update application status and notify student."""
    if not request.user.is_staff:
        return redirect('login')
    
    app = get_object_or_404(Application, id=app_id)
    
    # Validate status
    valid_statuses = ['Applied', 'Interview', 'Selected', 'Rejected']
    if status not in valid_statuses:
        messages.error(request, f"Invalid status: {status}")
        return redirect('admin_dash')
    
    # Update status
    app.status = status
    app.save()
    
    # Send notification
    try:
        result = notify_application_update(app)
        messages.success(
            request,
            f"Status updated to '{status}' and student notified"
        )
    except Exception as e:
        messages.warning(
            request,
            f"Status updated but notification failed: {str(e)}"
        )
    
    return redirect('admin_dash')
```

### Example 3: Bulk Notification for New Job

```python
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from portal.models import JobPosting, StudentProfile
from portal.utils import notify_new_job_posting

@login_required
def post_job_posting(request):
    """Create job posting and notify eligible students."""
    if not request.user.is_staff:
        return redirect('login')
    
    if request.method == 'POST':
        # Create job posting
        job = JobPosting.objects.create(
            title=request.POST['title'],
            company=request.POST['company'],
            description=request.POST['description'],
            min_cgpa=float(request.POST['min_cgpa']),
            deadline=request.POST['deadline'],
            job_type=request.POST['type'],
        )
        
        # Find eligible students
        eligible = StudentProfile.objects.filter(
            is_approved=True,
            cgpa__gte=job.min_cgpa
        )
        
        phones = [s.phone for s in eligible]
        
        # Notify them
        if phones:
            try:
                results = notify_new_job_posting(job, phones)
                messages.success(
                    request,
                    f"Job posted and {len(results['sent'])} students notified"
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"Job posted but notifications failed: {str(e)}"
                )
        else:
            messages.info(request, "Job posted but no eligible students to notify")
        
        return redirect('admin_dash')
```

---

## Error Handling Examples

### Graceful Error Handling

```python
from portal.utils import send_sms
import logging

logger = logging.getLogger(__name__)

def send_sms_with_fallback(phone, message, fallback_email=None):
    """Send SMS with email fallback."""
    try:
        result = send_sms(phone, message)
        if result['success']:
            logger.info(f"SMS sent to {phone}")
            return {'success': True, 'method': 'sms'}
        else:
            logger.warning(f"SMS failed: {result.get('error')}")
            # Fall back to email if provided
            if fallback_email:
                # Send email instead
                # (implement email logic here)
                return {'success': True, 'method': 'email'}
    except Exception as e:
        logger.error(f"SMS error: {str(e)}")
        if fallback_email:
            # Send email instead
            return {'success': True, 'method': 'email'}
        else:
            return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'No notification method available'}
```

### Retry with Exponential Backoff

```python
import time
from portal.utils import send_sms

def send_sms_with_backoff(phone, message, max_retries=5):
    """Send SMS with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            result = send_sms(phone, message)
            if result['success']:
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait longer each time: 1s, 2s, 4s, 8s, 16s
                wait = 2 ** attempt
                print(f"Attempt {attempt + 1} failed, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
    
    raise Exception(f"Failed to send SMS to {phone}")
```

---

## Testing Examples

### Unit Test Example

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from portal.models import StudentProfile
from portal.utils import send_sms, format_phone_e164

class SMSTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            usn='USN001',
            phone='9876543210',
            department='CS',
            cgpa=8.5,
            skills='Python, Django'
        )
    
    def test_format_phone(self):
        """Test phone formatting."""
        self.assertEqual(
            format_phone_e164('9876543210'),
            '+919876543210'
        )
        self.assertEqual(
            format_phone_e164('+919876543210'),
            '+919876543210'
        )
    
    def test_phone_format_with_student_phone(self):
        """Test formatting student's phone."""
        formatted = format_phone_e164(self.profile.phone)
        self.assertTrue(formatted.startswith('+'))
        self.assertIn('91', formatted)
```

### Integration Test Example

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from portal.models import StudentProfile
from unittest.mock import patch, MagicMock

class StudentApprovalTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        self.student = User.objects.create_user(
            username='student',
            password='studentpass'
        )
        self.profile = StudentProfile.objects.create(
            user=self.student,
            usn='USN001',
            phone='9876543210',
            department='CS',
            cgpa=8.5,
            skills='Python'
        )
    
    @patch('portal.utils.send_sms')
    def test_admin_approve_student_sends_sms(self, mock_send_sms):
        """Test that approving student sends SMS."""
        mock_send_sms.return_value = {
            'success': True,
            'message_id': 'SM123456789'
        }
        
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/admin/approve/{self.profile.id}/')
        
        # Check SMS was called
        mock_send_sms.assert_called_once()
        
        # Check student is approved
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_approved)
```

---

## Advanced Usage

### Async SMS Sending (with Celery)

```python
from celery import shared_task
from portal.utils import send_sms

@shared_task
def send_sms_async(phone, message):
    """Send SMS asynchronously."""
    try:
        result = send_sms(phone, message)
        return result
    except Exception as e:
        # Log error for retry
        send_sms_async.retry(exc=e, countdown=60)

# Usage in views
send_sms_async.delay(phone, message)
```

### SMS Queue Management

```python
from django.db import models
from django.utils import timezone

class SMSQueue(models.Model):
    phone = models.CharField(max_length=20)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"SMS to {self.phone}"

def process_sms_queue():
    """Process pending SMS from queue."""
    pending = SMSQueue.objects.filter(sent=False, attempts__lt=3)
    
    for sms in pending:
        try:
            result = send_sms(sms.phone, sms.message)
            if result['success']:
                sms.sent = True
                sms.save()
        except Exception as e:
            sms.attempts += 1
            sms.last_error = str(e)
            sms.save()
```

---

**These examples cover most use cases for SMS integration in your portal!**
