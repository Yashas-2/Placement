#!/usr/bin/env python
"""
Twilio Configuration Verification Script
Run this to check if your SMS setup is complete and correct.
Usage: python verify_sms_config.py
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_connect.settings')

import django
django.setup()

from django.conf import settings
from portal.utils import validate_twilio_credentials, format_phone_e164
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_env_file():
    """Check if .env file exists."""
    env_path = project_root / '.env'
    print("\n📋 Checking .env file...")
    
    if env_path.exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file NOT found at", env_path)
        print("  Create it by copying from the TWILIO_SETUP.md guide")
        return False


def check_credentials():
    """Check if Twilio credentials are configured."""
    print("\n🔐 Checking Twilio Credentials...")
    
    is_valid, error_msg = validate_twilio_credentials()
    
    if is_valid:
        print("✓ All credentials are configured")
        print(f"  • Account SID: {getattr(settings, 'TWILIO_ACCOUNT_SID', '')[:10]}...")
        print(f"  • Auth Token: {getattr(settings, 'TWILIO_AUTH_TOKEN', '')[:10]}...")
        print(f"  • Twilio Phone: {getattr(settings, 'TWILIO_PHONE_NUMBER', '')}")
        return True
    else:
        print("✗ Credentials missing or incomplete")
        print(f"  {error_msg}")
        return False


def check_settings():
    """Check Django settings for SMS configuration."""
    print("\n⚙️  Checking Django Settings...")
    
    checks = {
        'SMS_ENABLED': 'SMS Feature Enabled',
        'SMS_BATCH_SIZE': 'Batch Size',
        'SMS_RETRY_ATTEMPTS': 'Retry Attempts',
        'SMS_RETRY_DELAY': 'Retry Delay (seconds)',
        'SMS_DEFAULT_COUNTRY_CODE': 'Default Country Code',
    }
    
    all_ok = True
    for setting, label in checks.items():
        value = getattr(settings, setting, None)
        if value is not None:
            print(f"✓ {label}: {value}")
        else:
            print(f"✗ {label}: NOT SET")
            all_ok = False
    
    return all_ok


def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking Dependencies...")
    
    required_packages = {
        'twilio': 'Twilio SDK',
        'dotenv': 'Python-dotenv',
        'django': 'Django',
    }
    
    all_ok = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"✗ {name} is NOT installed")
            print(f"  Run: pip install {package}")
            all_ok = False
    
    return all_ok


def check_logs_directory():
    """Check if logs directory exists."""
    print("\n📝 Checking Logs Directory...")
    
    logs_dir = project_root / 'logs'
    if logs_dir.exists():
        print(f"✓ Logs directory exists: {logs_dir}")
        return True
    else:
        print(f"✗ Logs directory NOT found: {logs_dir}")
        try:
            logs_dir.mkdir(exist_ok=True)
            print(f"✓ Created logs directory: {logs_dir}")
            return True
        except Exception as e:
            print(f"✗ Failed to create logs directory: {e}")
            return False


def test_phone_formatting():
    """Test phone number formatting."""
    print("\n📱 Testing Phone Number Formatting...")
    
    test_cases = [
        ('9876543210', '+919876543210'),
        ('+919876543210', '+919876543210'),
        ('919876543210', '+919876543210'),
        ('+1234567890', '+1234567890'),
    ]
    
    all_ok = True
    for input_phone, expected in test_cases:
        result = format_phone_e164(input_phone)
        if result == expected:
            print(f"✓ {input_phone} → {result}")
        else:
            print(f"✗ {input_phone} → {result} (expected {expected})")
            all_ok = False
    
    return all_ok


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("TWILIO SMS CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    results = {
        '.env file': check_env_file(),
        'Twilio Credentials': check_credentials(),
        'Django Settings': check_settings(),
        'Dependencies': check_dependencies(),
        'Logs Directory': check_logs_directory(),
        'Phone Formatting': test_phone_formatting(),
    }
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ All checks passed! Your SMS setup is ready.")
        print("\nNext steps:")
        print("1. Run: python manage.py test_sms --phone 9876543210")
        print("2. Send a test SMS to verify everything works")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nFor help, see: TWILIO_SETUP.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
