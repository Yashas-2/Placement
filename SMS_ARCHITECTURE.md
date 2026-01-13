# Twilio SMS Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLACEMENT PORTAL                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐      ┌─────────────────────────────────┐ │
│  │   Admin Panel    │      │     Student Portal              │ │
│  │                  │      │                                 │ │
│  │ • Approve/Reject │      │ • Register Account              │ │
│  │   Students       │      │ • Apply for Jobs                │ │
│  │ • Post Jobs      │      │ • View Applications             │ │
│  │ • Update Status  │      │ • Edit Profile                  │ │
│  └────────┬─────────┘      └──────────────┬────────────────┘ │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
│                          │                                   │
│        ┌─────────────────▼──────────────────┐                │
│        │    Views Layer (views.py)          │                │
│        │                                    │                │
│        │ • admin_approve_student()          │                │
│        │ • admin_reject_student()           │                │
│        │ • update_application_status()      │                │
│        └─────────────────┬──────────────────┘                │
│                          │                                   │
│        ┌─────────────────▼──────────────────┐                │
│        │   SMS Utilities (utils.py)         │                │
│        │                                    │                │
│        │ • send_sms()                       │                │
│        │ • send_sms_bulk()                  │                │
│        │ • notify_*() functions             │                │
│        │ • format_phone_e164()              │                │
│        └─────────────────┬──────────────────┘                │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │   .env Configuration               │
         │                                    │
         │ TWILIO_ACCOUNT_SID                 │
         │ TWILIO_AUTH_TOKEN                  │
         │ TWILIO_PHONE_NUMBER                │
         │ SMS_ENABLED = True                 │
         │ SMS_BATCH_SIZE = 10                │
         │ SMS_RETRY_ATTEMPTS = 3             │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │   Django Settings (settings.py)    │
         │                                    │
         │ • Load env variables               │
         │ • Configure logging                │
         │ • Set SMS defaults                 │
         └─────────────────┬──────────────────┘
                           │
                           │
         ┌─────────────────▼──────────────────────────────┐
         │          TWILIO SMS API                        │
         │          (Cloud-based)                         │
         │                                                │
         │  https://api.twilio.com/2010-04-01/Accounts  │
         └─────────────────┬──────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │   STUDENT MOBILE DEVICES            │
         │                                    │
         │ Receives SMS Notifications         │
         │ On:                                │
         │ • Account Approval                 │
         │ • Account Rejection                │
         │ • Application Status Update        │
         │ • New Job Postings                 │
         └────────────────────────────────────┘
```

---

## Data Flow - Student Approval with SMS

```
┌──────────────────┐
│  Admin Clicks    │
│ "Approve" Button │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ admin_approve_student(request, id)   │
│ in views.py                          │
│                                      │
│ 1. Get student profile               │
│ 2. Set is_approved = True            │
│ 3. Set is_active = True              │
│ 4. Save to database                  │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ notify_student_approval(profile)     │
│ in utils.py                          │
│                                      │
│ Prepares message:                    │
│ "Congratulations! Your account..."   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ send_sms(phone, message)             │
│ in utils.py                          │
│                                      │
│ 1. Validate credentials              │
│ 2. Format phone to E.164             │
│ 3. Create Twilio client              │
│ 4. Send message                      │
│ 5. Handle errors with retry          │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ TWILIO API REQUEST                   │
│                                      │
│ POST /2010-04-01/Accounts/{SID}/Mes. │
│ From: TWILIO_PHONE_NUMBER            │
│ To: +919876543210                    │
│ Body: "Congratulations!..."          │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ TWILIO PROCESSES                     │
│                                      │
│ 1. Validate credentials              │
│ 2. Check account balance             │
│ 3. Route message to SMS network      │
│ 4. Return Message SID                │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ SMS DELIVERY                         │
│                                      │
│ Message delivered to student's       │
│ mobile phone via SMS network         │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ LOG ENTRY                            │
│ in logs/sms.log                      │
│                                      │
│ "[INFO] SMS sent successfully.       │
│  SID: SM1234567890abcdef..."         │
└──────────────────────────────────────┘
```

---

## Error Handling & Retry Logic

```
┌─────────────────────────────────┐
│ send_sms(to_number, message)    │
│ retry_count = 0                 │
└────────────┬────────────────────┘
             │
             ▼
     ┌───────────────┐
     │ SMS Enabled?  │
     └───┬───────┬───┘
         │       │
        No      Yes
         │       │
         │       ▼
         │   ┌─────────────────────┐
         │   │ Validate Credentials│
         │   └──────┬──────┬───────┘
         │          │      │
         │         OK    FAIL
         │          │      │
         │          │      └──→ Raise Exception
         │          │
         │          ▼
         │   ┌────────────────────┐
         │   │ Format Phone Number│
         │   └──────┬──────┬──────┘
         │          │      │
         │         OK   Invalid
         │          │      │
         │          │      └──→ Raise ValueError
         │          │
         │          ▼
         │   ┌────────────────────┐
         │   │ Call Twilio API    │
         │   └──────┬──────┬──────┘
         │          │      │
         │       Success  Error
         │          │      │
         │          │      ▼
         │          │   ┌─────────────┐
         │          │   │ Check Code  │
         │          │   └──┬────┬──┬──┘
         │          │      │    │  │
         │          │    429  5xx Other
         │          │   (Rate) (Srv) (error)
         │          │   Limit  Error  │
         │          │    │    │   │   │
         │          │   Yes  Yes  No  │
         │          │    │    │   │   │
         │          │    ▼    │   │   │
         │          │  Retry<─┘   │   │
         │          │   (Delay 5s)│   │
         │          │    │        │   │
         │          │ Retry<─────┘   │
         │          │  Count < Max   │
         │          │    │           │
         │          │   Yes         No
         │          │    │           │
         │          │    ▼           ▼
         │          │  Recurse    Return Error
         │          │              (Logged)
         │          │
         │          ▼
         │   ┌──────────────────────┐
         │   │ Return Success Dict  │
         │   │ {                    │
         │   │  'success': True,    │
         │   │  'message_id': '...' │
         │   │ }                    │
         │   └──────────────────────┘
         │
         └──→ Skip SMS (Log Info)
              Return Error Dict
```

---

## File Interaction Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    CONFIGURATION                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  .env (Secrets)                                          │
│  ├── TWILIO_ACCOUNT_SID                                 │
│  ├── TWILIO_AUTH_TOKEN                                  │
│  ├── TWILIO_PHONE_NUMBER                                │
│  └── SMS_* settings                                     │
│       │                                                  │
│       └──→ (read by django settings)                     │
│                                                          │
│  settings.py (Django Config)                             │
│  ├── Read .env values                                   │
│  ├── Configure TWILIO_* settings                        │
│  ├── Setup SMS defaults                                │
│  └── Configure logging to logs/sms.log                 │
│       │                                                  │
│       └──→ (imported by views and utils)                │
│                                                          │
└──────────────────────────────────────────────────────────┘
         │                    │
         │                    │
         ▼                    ▼
┌──────────────────┐   ┌──────────────────┐
│   views.py       │   │   utils.py       │
├──────────────────┤   ├──────────────────┤
│                  │   │                  │
│ Views that call: │   │ Core functions:  │
│                  │   │                  │
│ • admin_approve_ │   │ • send_sms()     │
│   student()      │   │ • send_sms_bulk()
│ • admin_reject_  │   │ • notify_*()     │
│   student()      │   │ • format_phone_  │
│ • update_        │   │   e164()         │
│   application_   │   │ • validate_      │
│   status()       │   │   credentials()  │
│                  │   │                  │
│ (calls notify_*) │   │ (uses settings)  │
│                  │   │ (logs to file)   │
│                  │   │                  │
└──────────────────┘   └──────────────────┘
         │                    │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  models.py         │
         ├────────────────────┤
         │                    │
         │ • StudentProfile   │
         │ • Application      │
         │ • JobPosting       │
         │                    │
         │ (provides data to  │
         │  pass to SMS fns)  │
         │                    │
         └────────────────────┘
         
         
┌──────────────────────────────────────────────────────────┐
│                    RUNTIME                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  logs/sms.log                                            │
│  ├── SMS activity logs                                  │
│  ├── Error messages with details                        │
│  ├── Success confirmations with Message IDs             │
│  └── Debugging info                                    │
│       │                                                  │
│       └──→ (managed by logging config in settings)       │
│                                                          │
│  management/commands/test_sms.py                         │
│  ├── Test SMS functionality                             │
│  ├── Validate phone formatting                          │
│  ├── Check credentials                                  │
│  └── Send test message                                 │
│       │                                                  │
│       └──→ (can be run: python manage.py test_sms)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## SMS Sending Process - Sequence Diagram

```
Admin        Django      utils.py      settings.py     Twilio       Student
  │            │             │              │            │            │
  │ Click       │             │              │            │            │
  ├─ Approve ──>│             │              │            │            │
  │            │ Validate    │              │            │            │
  │            ├────────────>│              │            │            │
  │            │             │ Read config  │            │            │
  │            │             ├─────────────>│            │            │
  │            │             │<──────────────┤            │            │
  │            │             │ (credentials) │            │            │
  │            │             │              │            │            │
  │            │             │ Format Phone │            │            │
  │            │             ├─ 9876543210 ─>           │            │
  │            │             │              │            │            │
  │            │             │ API Call     │            │            │
  │            │             ├─────────────────────────>│            │
  │            │             │              │            │ Process    │
  │            │             │              │            ├─ Check    │
  │            │             │              │            │  Balance  │
  │            │             │              │            ├─ Route    │
  │            │             │              │            │  Message  │
  │            │             │<────────────────────────────  Return   │
  │            │             │ (Message SID)│            │  SID      │
  │            │             │              │            │            │
  │            │             │ Log to file  │            │            │
  │            │ <──────────────────────────┤            │            │
  │            │ (success)   │              │            │            │
  │ Message    │             │              │            │   SMS Msg  │
  │<───────────┴─────────────┤              │            ├───────────>│
  │ "Success"  │             │              │            │            │
  │            │             │              │            │ Received! │
  │            │             │              │            │            │
```

---

## Configuration Priority (What Gets Used)

```
┌─────────────────────────────────────────────────────────┐
│  Setting: TWILIO_ACCOUNT_SID                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Priority Order:                                        │
│  1. Environment Variable (if set)                      │
│  2. Value from .env file                              │
│  3. Value in settings.py (default)                     │
│                                                         │
│  How it works:                                         │
│  • os.getenv('TWILIO_ACCOUNT_SID') is called first    │
│  • If not found, checks .env via python-dotenv        │
│  • If still not found, uses settings.py default       │
│                                                         │
│  Best Practice:                                        │
│  → Store in .env (most flexible)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Setting: SMS_ENABLED                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  If SMS_ENABLED = False:                               │
│  • send_sms() returns early                           │
│  • Logs "SMS is disabled"                             │
│  • No API calls to Twilio                            │
│  • Useful for testing/debugging                       │
│                                                         │
│  Current Value: True (SMS is ON)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Integration Points in Portal

```
┌─────────────────────────────────────────────────────┐
│           Student Registration Flow                 │
├─────────────────────────────────────────────────────┤
│                                                    │
│  1. Student fills form (email, phone, etc.)        │
│  2. Portal creates StudentProfile (is_approved=F)  │
│  3. Admin sees student in verification queue       │
│  4. Admin clicks "Approve"                         │
│  5. ──> SMS sent to student's phone                │
│      "Congratulations! Account approved"           │
│  6. Student can now login and apply for jobs      │
│                                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│        Student Rejection Flow                       │
├─────────────────────────────────────────────────────┤
│                                                    │
│  1. Student registration pending admin review      │
│  2. Admin clicks "Reject"                          │
│  3. ──> SMS sent to student's phone                │
│      "Registration rejected. Contact office"       │
│  4. StudentProfile is deleted                      │
│  5. Student cannot re-login                        │
│                                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│     Application Status Update Flow                  │
├─────────────────────────────────────────────────────┤
│                                                    │
│  1. Student applies for a job                      │
│  2. Application status = "Applied"                 │
│  3. Admin updates status (Selected/Rejected/etc.)  │
│  4. ──> SMS sent to student's phone                │
│      "Your status for XYZ Company updated to ..." │
│  5. Student receives notification instantly        │
│                                                    │
└─────────────────────────────────────────────────────┘
```

---

**This architecture ensures reliable, secure, and scalable SMS notifications!**
