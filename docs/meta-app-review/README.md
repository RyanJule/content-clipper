# Meta App Review Documentation

This folder contains all documentation required for Meta (Facebook/Instagram) app review approval.

## App Information

**App Name:** Content Clipper
**Website:** https://www.machine-systems.org
**Privacy Policy:** https://www.machine-systems.org/privacy-policy
**Terms of Service:** https://www.machine-systems.org/terms-of-service
**App Type:** Content Scheduling & Social Media Management
**Platform:** Web Application

## Overview

Content Clipper is a social media content scheduling platform that helps users manage and schedule their video content across multiple platforms, including Instagram. The app allows users to:

1. Upload and manage video clips
2. Schedule content for automatic posting
3. Manage comments and messages from their audience
4. Track performance with insights and analytics
5. Maintain consistent posting schedules

## Permissions Requested

We are requesting the following permissions for Instagram Graph API access:

| Permission | Use Case | Documentation |
|------------|----------|---------------|
| `public_profile` | Display user's basic Facebook profile information | [Use Case](./permission-use-cases.md#public_profile) |
| `pages_show_list` | List Facebook Pages managed by the user to connect Instagram Business accounts | [Use Case](./permission-use-cases.md#pages_show_list) |
| `instagram_basic` | Basic Instagram profile access | [Use Case](./permission-use-cases.md#instagram_basic) |
| `instagram_business_basic` | Access Instagram Business Account information | [Use Case](./permission-use-cases.md#instagram_business_basic) |
| `instagram_business_content_publish` | Create and publish posts, reels, and stories on Instagram | [Use Case](./permission-use-cases.md#instagram_business_content_publish) |
| `instagram_manage_comments` | Read, respond to, and moderate comments | [Use Case](./permission-use-cases.md#instagram_manage_comments) |
| `instagram_manage_messages` | Read and respond to Instagram Direct messages | [Use Case](./permission-use-cases.md#instagram_manage_messages) |
| `instagram_business_manage_messages` | Manage Instagram Business Direct messages | [Use Case](./permission-use-cases.md#instagram_business_manage_messages) |
| `instagram_business_manage_insights` | Access analytics and performance metrics | [Use Case](./permission-use-cases.md#instagram_business_manage_insights) |
| `pages_read_engagement` | Read engagement metrics for linked Facebook Pages | [Use Case](./permission-use-cases.md#pages_read_engagement) |
| `business_management` | Manage business assets and accounts | [Use Case](./permission-use-cases.md#business_management) |

## Testing Instructions

For detailed testing instructions, please see:
- [Test User Setup](./test-user-setup.md)
- [Step-by-Step Testing Guide](./testing-guide.md)
- [Demo Video Script](./demo-video-script.md)

## Test Credentials

Test accounts and credentials are provided in the app review submission form. For detailed setup instructions, see [Test User Setup](./test-user-setup.md).

## Key Features Demonstrated

1. **Content Publishing** - Schedule and publish video content to Instagram
2. **Comment Management** - View and respond to comments on posts
3. **Message Management** - Handle direct messages from followers
4. **Analytics Dashboard** - View insights and performance metrics
5. **Account Management** - Connect and manage multiple Instagram Business accounts

## Privacy & Data Handling

- All access tokens are encrypted using Fernet encryption (AES-128)
- User data is stored securely in PostgreSQL database
- Users can disconnect their accounts at any time
- Data deletion requests are handled within 30 days
- Full privacy policy: https://www.machine-systems.org/privacy-policy

## Support Contact

**Email:** ryanjulemcdowell@gmail.com
**Support Email:** support@contentclipper.com
**Response Time:** Within 24-48 hours

## Technical Implementation

- **Backend:** FastAPI (Python)
- **Frontend:** React
- **Database:** PostgreSQL
- **Authentication:** JWT + OAuth 2.0
- **Hosting:** Machine Systems

## Files in This Directory

- `README.md` - This file
- `permission-use-cases.md` - Detailed use cases for each permission
- `testing-guide.md` - Step-by-step instructions for reviewers
- `test-user-setup.md` - How to set up test accounts
- `demo-video-script.md` - Script for demo video
- `screenshots/` - Screenshots demonstrating each feature

## Version History

- **v1.0.0** (2025-11-10) - Initial app review submission
