#!/usr/bin/env python3
"""
Check OAuth Configuration for Content Clipper

This script checks if OAuth credentials are properly configured
without exposing the actual secret values.

Usage:
    python scripts/check_oauth_config.py

Or from backend directory:
    python -m app.check_config
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.core.config import settings

    def mask_value(value: str, show_chars: int = 4) -> str:
        """Show first and last N characters, mask the middle"""
        if not value:
            return "❌ NOT SET"
        if len(value) <= show_chars * 2:
            return f"✓ {value[:2]}...{value[-2:]} (length: {len(value)})"
        return f"✓ {value[:show_chars]}...{value[-show_chars:]} (length: {len(value)})"

    print("\n" + "="*70)
    print("Content Clipper OAuth Configuration Check")
    print("="*70)

    print("\n📍 Environment Settings:")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Backend URL: {settings.BACKEND_URL}")
    print(f"  Frontend URL: {settings.FRONTEND_URL}")

    print("\n📸 Instagram/Facebook OAuth:")
    print(f"  Client ID: {mask_value(settings.INSTAGRAM_CLIENT_ID)}")
    print(f"  Client Secret: {'✓ SET' if settings.INSTAGRAM_CLIENT_SECRET else '❌ NOT SET'}")
    if settings.INSTAGRAM_CLIENT_SECRET:
        print(f"  Client Secret Length: {len(settings.INSTAGRAM_CLIENT_SECRET)}")

    print("\n🎥 YouTube OAuth:")
    print(f"  Client ID: {'✓ SET' if settings.YOUTUBE_CLIENT_ID else '❌ NOT SET'}")
    print(f"  Client Secret: {'✓ SET' if settings.YOUTUBE_CLIENT_SECRET else '❌ NOT SET'}")

    print("\n💼 LinkedIn OAuth:")
    print(f"  Client ID: {'✓ SET' if settings.LINKEDIN_CLIENT_ID else '❌ NOT SET'}")
    print(f"  Client Secret: {'✓ SET' if settings.LINKEDIN_CLIENT_SECRET else '❌ NOT SET'}")

    print("\n🔐 Security:")
    print(f"  Fernet Key: {'✓ SET' if settings.FERNET_KEY else '❌ NOT SET'}")
    print(f"  Secret Key: {'✓ SET' if settings.SECRET_KEY else '❌ NOT SET'}")

    # Validation
    print("\n" + "="*70)
    print("Validation Results:")
    print("="*70)

    issues = []

    if not settings.INSTAGRAM_CLIENT_ID:
        issues.append("❌ INSTAGRAM_CLIENT_ID is not set")
    elif len(settings.INSTAGRAM_CLIENT_ID) < 10:
        issues.append(f"⚠️  INSTAGRAM_CLIENT_ID seems too short ({len(settings.INSTAGRAM_CLIENT_ID)} chars)")

    if not settings.INSTAGRAM_CLIENT_SECRET:
        issues.append("❌ INSTAGRAM_CLIENT_SECRET is not set")
    elif len(settings.INSTAGRAM_CLIENT_SECRET) < 10:
        issues.append(f"⚠️  INSTAGRAM_CLIENT_SECRET seems too short ({len(settings.INSTAGRAM_CLIENT_SECRET)} chars)")

    if not settings.FERNET_KEY:
        issues.append("❌ FERNET_KEY is not set (required for encrypting tokens)")

    if issues:
        print("\n⚠️  Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 To fix:")
        print("  1. Make sure you have a .env file in the project root")
        print("  2. Add INSTAGRAM_CLIENT_ID and INSTAGRAM_CLIENT_SECRET from https://developers.facebook.com/apps")
        print("  3. Generate FERNET_KEY with: python scripts/generate_fernet_key.py")
        print("  4. Restart your Docker containers: docker-compose restart backend")
    else:
        print("\n✅ All required Instagram OAuth credentials are configured!")
        print("\n📋 OAuth Callback URL for Facebook App:")
        print(f"  {settings.BACKEND_URL}/api/v1/oauth/instagram/callback")
        print("\n💡 Make sure this URL is added to your Facebook App's Valid OAuth Redirect URIs")

    print("\n" + "="*70 + "\n")

except ImportError as e:
    print(f"\n❌ Error importing settings: {e}")
    print("\nMake sure you're running this from the project root:")
    print("  python scripts/check_oauth_config.py")
    print("\nOr from the backend directory:")
    print("  cd backend && python -c 'from app.core.config import settings; print(settings.INSTAGRAM_CLIENT_ID)'")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
