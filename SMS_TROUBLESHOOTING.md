# Twilio SMS Troubleshooting Guide

## Quick Diagnostics

### Run Configuration Verification
```bash
python verify_sms_config.py
```
This will check everything and show what's configured correctly.

### Run SMS Test
```bash
python manage.py test_sms --phone 9876543210
```
This sends a real test SMS to see if everything works.

---

## Common Issues & Solutions

### 1. "Missing Twilio credentials"

**Error Message:**
```
Missing Twilio credentials: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
```

**Cause:** 
- .env file not created or missing credentials
- Credentials in settings.py are empty

**Solution:**
1. Create `.env` file in project root (copy from example below)
2. Add your actual Twilio credentials:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+1234567890
   ```
3. Get credentials from https://www.twilio.com/console
4. Restart Django: Press Ctrl+C and run server again

---

### 2. "Invalid 'To' Phone Number"

**Error Message:**
```
Twilio Error 21211: Invalid 'To' Phone Number
```

**Cause:**
- Phone number not in E.164 format
- Phone number doesn't exist or is inactive
- Leading zeros not removed

**Valid Formats:**
- ✓ `9876543210` (10 digits)
- ✓ `+919876543210` (with country code)
- ✓ `919876543210` (country code without +)

**Invalid Formats:**
- ✗ `09876543210` (leading zero)
- ✗ `+91 9876543210` (space)
- ✗ `+91-9876543210` (dash)
- ✗ `9876543210 ` (trailing space)

**Solution:**
```python
from portal.utils import format_phone_e164

# All these will format correctly
formatted = format_phone_e164('9876543210')      # → +919876543210
formatted = format_phone_e164('+919876543210')   # → +919876543210
formatted = format_phone_e164('919876543210')    # → +919876543210
```

---

### 3. "Authentication Error"

**Error Message:**
```
Twilio Error 20003: Authentication Error
```

**Cause:**
- Wrong Account SID or Auth Token
- Credentials are truncated or have typos
- Credentials have extra spaces

**Solution:**
1. Go to https://www.twilio.com/console
2. Copy exact values (nothing extra):
   - Account SID: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Auth Token: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. Paste into `.env` without extra spaces
4. Test: `python manage.py test_sms --phone 9876543210`

**Check for hidden characters:**
```python
import os
from dotenv import load_dotenv
load_dotenv()

sid = os.getenv('TWILIO_ACCOUNT_SID')
token = os.getenv('TWILIO_AUTH_TOKEN')

print(f"SID: '{sid}' (length: {len(sid)})")
print(f"Token: '{token}' (length: {len(token)})")
```

---

### 4. "Rate Limit Exceeded (429)"

**Error Message:**
```
Twilio Error 429: Rate limit exceeded
```

**Cause:**
- Sending too many SMS too fast
- Not enough delay between messages
- Batch size too large

**Solution:**
1. System automatically retries after 5 seconds
2. Adjust in `.env`:
   ```env
   SMS_BATCH_SIZE=5        # Instead of 10
   SMS_RETRY_DELAY=10      # Instead of 5 (seconds)
   ```
3. Reduce frequency of bulk sends
4. Spread messages over time

**Example:**
```python
# Good: Send in batches with delay
from portal.utils import send_sms_bulk
import time

groups = [phones[i:i+5] for i in range(0, len(phones), 5)]
for group in groups:
    send_sms_bulk(group, message)
    time.sleep(2)
```

---

### 5. "Server Error (5xx)"

**Error Message:**
```
Twilio Error 500: Server Error
Twilio Error 503: Service Unavailable
```

**Cause:**
- Temporary Twilio server issue
- Network connectivity problem
- API is down

**Solution:**
- System automatically retries (up to 3 times)
- Wait a few minutes and try again
- Check Twilio Status: https://status.twilio.com/
- Errors are logged in `logs/sms.log`

---

### 6. "SMS Not Received by Student"

**Symptoms:**
- No error in logs
- SMS ID returned
- But student didn't receive SMS

**Possible Causes:**
1. Phone number is invalid
2. Network provider issue
3. Message blocked by phone
4. Twilio number not verified for country

**Diagnosis Steps:**
1. Check logs: `tail -f logs/sms.log`
2. Verify phone number is real and active
3. Test with different phone number
4. Check Twilio Console > Messages > Logs
5. Check if phone blocked SMS from unknown numbers

**Solution:**
- Ask student to check spam folder
- Verify phone number with student
- Try again after a few minutes
- Contact Twilio support if persistent

---

### 7. "SMS_ENABLED is False"

**Error:**
```
SMS is disabled. Message not sent.
```

**Cause:**
- `SMS_ENABLED=False` in `.env`

**Solution:**
```env
SMS_ENABLED=True
```

**When to disable SMS:**
- Testing without Twilio
- Development environment
- During maintenance

---

### 8. "Logs Directory Not Found"

**Error:**
```
[ERROR] Failed to create logs directory
```

**Cause:**
- No write permission to project directory
- Permissions issue

**Solution:**
```bash
# Create logs directory manually
mkdir logs

# On Windows
mkdir logs

# Verify
ls -la logs/          # Should exist now
```

---

### 9. "Module Not Found: twilio"

**Error:**
```
ModuleNotFoundError: No module named 'twilio'
```

**Cause:**
- Twilio package not installed

**Solution:**
```bash
pip install twilio==9.0.4

# Or install all dependencies
pip install -r requirements.txt

# Verify
python -c "import twilio; print(twilio.__version__)"
```

---

### 10. "python-dotenv Not Found"

**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Cause:**
- python-dotenv package not installed

**Solution:**
```bash
pip install python-dotenv==1.0.0

# Or install all dependencies
pip install -r requirements.txt
```

---

## Debugging Tips

### Check If Credentials are Loaded

```python
from django.conf import settings

print(f"Account SID: {getattr(settings, 'TWILIO_ACCOUNT_SID', 'NOT SET')}")
print(f"Auth Token: {getattr(settings, 'TWILIO_AUTH_TOKEN', 'NOT SET')}")
print(f"Phone: {getattr(settings, 'TWILIO_PHONE_NUMBER', 'NOT SET')}")
print(f"SMS Enabled: {getattr(settings, 'SMS_ENABLED', 'NOT SET')}")
```

### Test SMS Directly in Python Shell

```bash
python manage.py shell
```

```python
from portal.utils import send_sms, format_phone_e164

# Format a phone number
phone = format_phone_e164('9876543210')
print(f"Formatted: {phone}")

# Send test SMS
try:
    result = send_sms(phone, "Test message")
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
```

### Monitor Logs in Real Time

**Linux/Mac:**
```bash
tail -f logs/sms.log
```

**Windows:**
```cmd
type logs\sms.log
```

**Or in Python:**
```python
with open('logs/sms.log', 'r') as f:
    print(f.read())
```

### Enable Debug Logging

In `settings.py`:
```python
LOGGING = {
    'loggers': {
        'portal.utils': {
            'level': 'DEBUG',  # More verbose
        },
    },
}
```

### Check Twilio Account Balance

1. Go to https://www.twilio.com/console
2. Look for "Account Balance" on dashboard
3. Should show your remaining credits
4. Free trial: $15 (≈1000 SMS to India)

---

## Prevention Tips

### 1. Validate Phone Before SMS
```python
def is_valid_phone(phone):
    """Quick validation of phone format."""
    clean = str(phone).replace('+', '').replace('-', '').replace(' ', '')
    return clean.isdigit() and len(clean) >= 10

# Usage
if is_valid_phone(student.phone):
    send_sms(student.phone, message)
```

### 2. Add Try-Except to All SMS Calls
```python
try:
    result = send_sms(phone, message)
    if result['success']:
        # Log success
        logger.info(f"SMS sent to {phone}")
    else:
        # Log failure reason
        logger.warning(f"SMS failed: {result.get('error')}")
except Exception as e:
    # Log exception details
    logger.exception(f"SMS error: {str(e)}")
```

### 3. Queue SMS for Async Sending
```python
# Consider using Celery for large bulk sends
from celery import shared_task

@shared_task
def send_sms_async(phone, message):
    """Send SMS in background."""
    send_sms(phone, message)

# Usage
send_sms_async.delay(phone, message)
```

### 4. Monitor Costs
- Check Twilio Console monthly
- Set spending alerts in Twilio Console
- Track costs per feature

### 5. Test Regularly
```bash
# Weekly test
python manage.py test_sms --phone YOUR_PHONE
```

---

## Getting Professional Help

### Check Twilio Documentation
- https://www.twilio.com/docs/sms
- https://github.com/twilio/twilio-python

### Contact Support
- Twilio Support: https://support.twilio.com
- Community Forum: https://www.twilio.com/community

### Check Portal Logs
```bash
# View SMS logs
logs/sms.log

# View Django logs
# Check LOGGING configuration in settings.py
```

---

## Checklist Before Going to Production

- [ ] All credentials set in `.env`
- [ ] `.env` added to `.gitignore`
- [ ] `python verify_sms_config.py` shows ✓ all checks
- [ ] `python manage.py test_sms --phone` works
- [ ] Tested approval notification works
- [ ] Tested rejection notification works
- [ ] Tested status update notification works
- [ ] Logs are being written to `logs/sms.log`
- [ ] Error handling is in place in views
- [ ] User gets feedback when SMS fails
- [ ] Twilio account has sufficient balance
- [ ] Logging is configured for monitoring

---

## Quick Reference Commands

```bash
# Verify configuration
python verify_sms_config.py

# Test SMS
python manage.py test_sms --phone 9876543210

# Check logs
tail -f logs/sms.log              # Linux/Mac
type logs\sms.log                 # Windows

# Install dependencies
pip install -r requirements.txt

# Django shell for testing
python manage.py shell

# Run server
python manage.py runserver
```

---

**Last Updated**: January 2026
**Contact**: Check TWILIO_SETUP.md for support resources
