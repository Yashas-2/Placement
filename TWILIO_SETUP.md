# Twilio SMS Setup Guide

## Overview
This guide helps you set up Twilio SMS integration for the Placement Portal to send automatic notifications to students.

## Prerequisites
- Python 3.8+
- Django 6.0+
- Twilio account (free tier available)

## Step 1: Create a Twilio Account

1. Go to [https://www.twilio.com/](https://www.twilio.com/)
2. Sign up for a free account
3. Verify your phone number
4. You'll get free credits ($15) to test

## Step 2: Get Your Twilio Credentials

1. Log in to [Twilio Console](https://www.twilio.com/console)
2. Find your credentials on the dashboard:
   - **Account SID** - Your unique account identifier
   - **Auth Token** - Your authentication token
3. Get a **Twilio Phone Number**:
   - Go to "Phone Numbers" → "Manage" → "Active Numbers"
   - Or create a new one in "Phone Numbers" → "Manage" → "Buy a Number"
   - Choose a number and note it (e.g., +1234567890)

## Step 3: Configure Environment Variables

### Option A: Using .env file (Recommended)

Edit the `.env` file in your project root:

```env
# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_account_sid_from_console
TWILIO_AUTH_TOKEN=your_auth_token_from_console
TWILIO_PHONE_NUMBER=+1234567890

# SMS Settings
SMS_ENABLED=True
SMS_DEFAULT_COUNTRY_CODE=+91
SMS_BATCH_SIZE=10
SMS_RETRY_ATTEMPTS=3
SMS_RETRY_DELAY=5
```

### Option B: Using System Environment Variables

**On Windows (Command Prompt as Administrator):**
```cmd
setx TWILIO_ACCOUNT_SID "your_account_sid"
setx TWILIO_AUTH_TOKEN "your_auth_token"
setx TWILIO_PHONE_NUMBER "+1234567890"
```

**On Windows (PowerShell as Administrator):**
```powershell
[Environment]::SetEnvironmentVariable("TWILIO_ACCOUNT_SID", "your_account_sid", "User")
[Environment]::SetEnvironmentVariable("TWILIO_AUTH_TOKEN", "your_auth_token", "User")
[Environment]::SetEnvironmentVariable("TWILIO_PHONE_NUMBER", "+1234567890", "User")
```

**On Linux/Mac:**
```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_PHONE_NUMBER="+1234567890"
```

## Step 4: Install Required Packages

```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install twilio==9.0.4
pip install python-dotenv==1.0.0
```

## Step 5: Verify Configuration

### Test via Django Management Command

```bash
python manage.py test_sms --phone 9876543210
```

Or with full number:
```bash
python manage.py test_sms --phone +919876543210
```

**Expected Output:**
```
Testing Twilio SMS Configuration...
------------------------------------------------------------
Step 1: Validating credentials...
✓ Credentials are configured
  Account SID: AC5e38a27f...
  Twilio Number: +1234567890

Step 2: Formatting phone number...
✓ Formatted: +919876543210

Step 3: Sending test SMS...
✓ SMS sent successfully!
  Message ID: SM1234567890abcdef1234567890abcdef
  To: +919876543210
------------------------------------------------------------
Test complete!
```

### Check Logs

SMS activity is logged to `logs/sms.log`. Check recent logs:

```bash
# On Windows
type logs\sms.log

# On Linux/Mac
tail -f logs/sms.log
```

## Step 6: Features & Usage

### Available SMS Functions

#### 1. Send Single SMS
```python
from portal.utils import send_sms

result = send_sms('+919876543210', 'Your message here')
if result['success']:
    print(f"Message ID: {result['message_id']}")
```

#### 2. Bulk SMS
```python
from portal.utils import send_sms_bulk

recipients = ['+919876543210', '+919876543211', '+919876543212']
results = send_sms_bulk(recipients, 'Message to multiple people')
print(f"Sent: {len(results['sent'])}, Failed: {len(results['failed'])}")
```

#### 3. Notify Student Approval
```python
from portal.utils import notify_student_approval

notify_student_approval(student_profile)
```

#### 4. Notify Application Update
```python
from portal.utils import notify_application_update

notify_application_update(application)
```

#### 5. Notify New Job Posting
```python
from portal.utils import notify_new_job_posting

student_phones = ['+919876543210', '+919876543211']
notify_new_job_posting(job_posting, student_phones)
```

## Step 7: Production Configuration

### Security Considerations

1. **Never commit credentials**:
   - Add `.env` to `.gitignore`
   - Use environment variables only

2. **Use strong Auth Token**:
   - Rotate tokens regularly in Twilio Console
   - Revoke compromised tokens immediately

3. **Rate Limiting**:
   - Default: 10 SMS per batch with 1-second delay
   - Adjust `SMS_BATCH_SIZE` in `.env` if needed

4. **Logging**:
   - All SMS activities logged to `logs/sms.log`
   - Check logs for failures and errors

### Phone Number Verification (India)

For Indian numbers, ensure:
- Country code is correct: `+91`
- 10-digit number after country code
- Format examples:
  - ✓ `9876543210` → `+919876543210`
  - ✓ `+919876543210` → `+919876543210`
  - ✗ `019876543210` (leading zero - will be stripped)

### Error Handling

The system automatically retries failed messages:
- Max retries: 3 (configurable via `SMS_RETRY_ATTEMPTS`)
- Delay between retries: 5 seconds (configurable via `SMS_RETRY_DELAY`)
- Retryable errors: Rate limits (429), Server errors (5xx)

## Step 8: Integration Points

The SMS system automatically sends messages in these scenarios:

1. **Student Approval**: When admin approves a student account
2. **Student Rejection**: When admin rejects a student
3. **Application Status Update**: When admin updates job application status
4. **New Job Posting**: Notify eligible students (when implemented)

## Troubleshooting

### Issue: "Missing Twilio credentials"
**Solution**: Verify all three credentials are set in `.env`:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

### Issue: "Invalid phone number format"
**Solution**: Use E.164 format or let the system auto-format:
- Good: `9876543210` or `+919876543210`
- Bad: `9876543210 `, ` 9876543210`, `09876543210`

### Issue: "Twilio Error 21211: Invalid 'To' Phone Number"
**Solution**: 
1. Check phone number is in E.164 format
2. Verify it's a real, active mobile number
3. For testing, use your own phone number

### Issue: "Twilio Error 20003: Authentication Error"
**Solution**: 
1. Verify Account SID and Auth Token are correct
2. Check they're not truncated or have extra spaces
3. Regenerate token in Twilio Console if needed

### Issue: "No logs appearing"
**Solution**:
1. Check `logs/` directory exists
2. Verify write permissions on the directory
3. Check `SMS_ENABLED=True` in settings

## Monitoring & Alerts

### View Message Status
```bash
python manage.py shell
from portal.utils import send_sms
# Check SMS logs in logs/sms.log
```

### Set Up Twilio Alerts
1. Go to Twilio Console
2. Settings → Alerts & Notifications
3. Configure email alerts for failures

## Cost Estimation

- **India**: ₹1-2 per SMS (approximately $0.01-0.03 USD)
- **Free trial**: $15 credit (≈ 750-1500 SMS to India)
- **Upgrade**: Pay-as-you-go pricing after trial

## Support

- [Twilio Documentation](https://www.twilio.com/docs/)
- [Twilio Python SDK](https://github.com/twilio/twilio-python)
- [SMS API Reference](https://www.twilio.com/docs/sms)

---

**Last Updated**: January 2026
**Tested with**: Django 6.0, Twilio 9.0.4, Python 3.10+
