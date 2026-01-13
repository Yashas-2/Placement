# Twilio SMS Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### 2. Get Twilio Credentials (2 minutes)
- Go to https://www.twilio.com/console
- Copy your **Account SID** and **Auth Token**
- Get a **Phone Number** from "Phone Numbers" section

### 3. Configure .env File (1 minute)
Edit `.env` in your project root:
```env
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number

SMS_ENABLED=True
SMS_DEFAULT_COUNTRY_CODE=+91
```

### 4. Verify Setup (1 minute)
```bash
python verify_sms_config.py
```

### 5. Test SMS (instant)
```bash
python manage.py test_sms --phone 9876543210
```

---

## ✅ SMS is Now Live!

Your placement portal can now:
- ✓ Send approval notifications to students
- ✓ Send rejection notifications
- ✓ Update students on application status
- ✓ Notify about new job postings

---

## 🔧 Common Tasks

### Send SMS to a Student
```python
from portal.utils import send_sms

send_sms('+919876543210', 'Your message here')
```

### Notify Multiple Students
```python
from portal.utils import send_sms_bulk

phones = ['+919876543210', '+919876543211']
send_sms_bulk(phones, 'Message for everyone')
```

### Check SMS Logs
```bash
# View recent SMS activity
tail -f logs/sms.log

# On Windows
type logs\sms.log
```

---

## ⚠️ Important Notes

1. **Keep credentials secret** - Never share your Account SID or Auth Token
2. **Add .env to .gitignore** - It's already configured, don't remove it
3. **Free trial credit** - You get $15 to test (≈1000 SMS to India)
4. **Phone numbers** - Use format: 9876543210 or +919876543210

---

## 📖 Full Documentation

For detailed information, see [TWILIO_SETUP.md](TWILIO_SETUP.md)

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Missing Twilio credentials" | Check .env file has all 3 credentials |
| "Invalid 'To' Phone Number" | Use format: 9876543210 or +919876543210 |
| "Authentication Error" | Verify Account SID and Auth Token are correct |
| "No SMS logs" | Run `python verify_sms_config.py` to diagnose |

---

**Ready to send SMS?** → Run `python manage.py test_sms --phone 9876543210`
