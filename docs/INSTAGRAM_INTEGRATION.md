# Instagram Integration Documentation

This document provides technical documentation for the Instagram Graph API integration in Content Clipper.

## Overview

Content Clipper integrates with Instagram Graph API to provide comprehensive Instagram Business account management, including:

- Content publishing (images, videos, reels, carousels, stories)
- Comment management and moderation
- Direct message handling
- Analytics and insights
- Account management

## Architecture

### Backend Components

#### 1. Instagram Graph API Service
**File:** `backend/app/services/instagram_graph_service.py`

Core service that handles all Instagram Graph API interactions.

**Key Classes:**
- `InstagramGraphAPI`: Main API client
- `InstagramGraphAPIError`: Custom exception for API errors

**Key Methods:**

Publishing:
- `create_image_container()` - Create container for image posts
- `create_video_container()` - Create container for video/reel posts
- `create_carousel_container()` - Create container for carousel posts
- `create_story_container()` - Create container for stories
- `publish_container()` - Publish a media container
- `check_container_status()` - Check video processing status

Comments:
- `get_media_comments()` - Get comments on a post
- `reply_to_comment()` - Reply to a comment
- `delete_comment()` - Delete a comment
- `hide_comment()` - Hide/unhide a comment

Messages:
- `get_conversations()` - Get DM conversations
- `get_conversation_messages()` - Get messages in a conversation
- `send_message()` - Send a direct message

Insights:
- `get_account_insights()` - Get account-level analytics
- `get_media_insights()` - Get post-level analytics
- `get_story_insights()` - Get story analytics
- `get_page_insights()` - Get Facebook Page analytics

Account:
- `get_facebook_pages()` - List Facebook Pages with Instagram accounts
- `get_instagram_account_info()` - Get account information
- `get_user_media()` - Get published media
- `get_media_details()` - Get details about a media object

#### 2. OAuth Service
**File:** `backend/app/services/oauth_service.py`

Handles OAuth authentication with Facebook/Instagram.

**Class:** `InstagramOAuth`

**Key Features:**
- Uses Facebook OAuth (required for Instagram Business API)
- Requests all 11 required permissions
- Retrieves Instagram Business Account ID from Facebook Pages
- Stores Page access token for API calls
- Handles account linking between Facebook Pages and Instagram

**Permissions Requested:**
1. `public_profile` - Basic Facebook profile
2. `pages_show_list` - List managed Facebook Pages
3. `instagram_basic` - Basic Instagram access
4. `instagram_business_basic` - Instagram Business account info
5. `instagram_business_content_publish` - Publish content
6. `instagram_manage_comments` - Manage comments
7. `instagram_manage_messages` - Manage messages (legacy)
8. `instagram_business_manage_messages` - Manage business messages
9. `instagram_business_manage_insights` - Access analytics
10. `pages_read_engagement` - Read page engagement
11. `business_management` - Manage business assets

#### 3. Social Service
**File:** `backend/app/services/social_service.py`

Orchestrates content publishing workflow.

**Key Functions:**
- `publish_post()` - Main publishing function (async)
- `_publish_to_instagram()` - Instagram-specific publishing logic

**Publishing Flow:**
1. Validate post and clip exist
2. Get connected Instagram account
3. Decrypt access token
4. Determine media type (image/video)
5. Create appropriate media container
6. For videos: wait for processing to complete
7. Publish container to Instagram
8. Update post status and store Instagram URL

#### 4. API Endpoints
**File:** `backend/app/api/v1/endpoints/oauth.py`

OAuth-related endpoints:
- `GET /api/v1/oauth/{platform}/authorize` - Start OAuth flow
- `GET /api/v1/oauth/{platform}/callback` - OAuth callback handler
- `POST /api/v1/oauth/{platform}/disconnect` - Disconnect account
- `GET /api/v1/oauth/{platform}/status` - Check connection status
- `GET /api/v1/oauth/instagram/available-accounts` - List available accounts

**File:** `backend/app/api/v1/endpoints/social.py`

Social media post management:
- `POST /api/v1/social/` - Create post
- `GET /api/v1/social/` - List posts
- `GET /api/v1/social/{post_id}` - Get post details
- `PUT /api/v1/social/{post_id}` - Update post
- `DELETE /api/v1/social/{post_id}` - Delete post
- `POST /api/v1/social/{post_id}/publish` - Publish post

### Frontend Components

#### 1. OAuth Connect Modal
**File:** `frontend/src/components/Accounts/OAuthConnectModal.jsx`

Handles OAuth popup flow for connecting Instagram accounts.

**Features:**
- Opens popup window for OAuth authorization
- Uses `postMessage` API for secure communication
- Handles success/error callbacks
- Closes popup on completion

#### 2. Instagram Account Selector
**File:** `frontend/src/components/Accounts/InstagramAccountSelector.jsx`

Allows users to select which Instagram account to connect when they have multiple Facebook Pages.

**Features:**
- Lists all available Instagram Business accounts
- Shows profile pictures, usernames, and follower counts
- Allows single selection
- Handles cases with no Instagram accounts
- Provides helpful links for account setup

#### 3. Account Card
**File:** `frontend/src/components/Accounts/AccountCard.jsx`

Displays connected Instagram account information.

**Features:**
- Shows platform icon and username
- Displays active/inactive status
- Provides disconnect option

### Database Schema

#### Accounts Table

Stores connected social media accounts:

```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50),
    account_username VARCHAR(255),
    access_token_enc TEXT,  -- Fernet encrypted
    refresh_token_enc TEXT,  -- Fernet encrypted
    token_expires_at TIMESTAMP,
    connected_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    meta_info JSONB  -- Stores instagram_business_account_id, etc.
);
```

**meta_info Structure for Instagram:**
```json
{
  "id": "instagram_account_id",
  "username": "instagram_username",
  "name": "display_name",
  "profile_picture_url": "url",
  "facebook_user_id": "fb_user_id",
  "facebook_page_id": "page_id",
  "facebook_page_name": "page_name",
  "instagram_business_account_id": "ig_business_account_id",
  "access_token": "page_access_token"
}
```

#### Social Posts Table

Stores scheduled and published posts:

```sql
CREATE TABLE social_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    clip_id INTEGER REFERENCES clips(id),
    platform VARCHAR(50),
    title TEXT,
    caption TEXT,
    hashtags TEXT,  -- JSON array as string
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP,
    status VARCHAR(20),  -- draft, scheduled, publishing, published, failed
    platform_post_id VARCHAR(255),  -- Instagram media ID
    platform_url TEXT,  -- Instagram post permalink
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# Facebook/Instagram App Credentials
INSTAGRAM_CLIENT_ID=your_facebook_app_id
INSTAGRAM_CLIENT_SECRET=your_facebook_app_secret

# URLs
BACKEND_URL=https://machine-systems.org
FRONTEND_URL=https://machine-systems.org

# Encryption
FERNET_KEY=your_fernet_key_here

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (for OAuth state)
REDIS_URL=redis://localhost:6379/0
```

### Meta Developer App Setup

1. **Create Facebook App:**
   - Go to https://developers.facebook.com/apps
   - Click "Create App"
   - Choose "Business" type
   - Fill in app details

2. **Add Instagram Graph API:**
   - In app dashboard, click "Add Product"
   - Select "Instagram Graph API"
   - Complete setup

3. **Configure OAuth Settings:**
   - Go to App Settings > Basic
   - Add App Domains: `machine-systems.org`
   - Go to Instagram > Basic Display
   - Add Valid OAuth Redirect URIs:
     - `https://www.machine-systems.org/api/v1/oauth/instagram/callback`

4. **Request Permissions:**
   - Go to App Review > Permissions and Features
   - Request each of the 11 permissions listed above
   - Provide use case documentation (see `docs/meta-app-review/`)

5. **Get Credentials:**
   - Copy App ID → `INSTAGRAM_CLIENT_ID`
   - Copy App Secret → `INSTAGRAM_CLIENT_SECRET`

## Usage Examples

### Publishing a Post

```python
from app.services.instagram_graph_service import InstagramGraphAPI

# Initialize API client
ig_api = InstagramGraphAPI(access_token)

# Create video container
container_id = await ig_api.create_video_container(
    ig_account_id="123456789",
    video_url="https://example.com/video.mp4",
    caption="Check out this awesome video! #content #creator",
    media_type="REELS"
)

# Wait for video processing
status = await ig_api.check_container_status(container_id)
while status.get("status_code") != "FINISHED":
    await asyncio.sleep(2)
    status = await ig_api.check_container_status(container_id)

# Publish
media_id = await ig_api.publish_container(
    ig_account_id="123456789",
    creation_id=container_id
)

# Get permalink
details = await ig_api.get_media_details(media_id)
permalink = details.get("permalink")
```

### Managing Comments

```python
# Get comments on a post
comments = await ig_api.get_media_comments(media_id="987654321")

# Reply to a comment
reply_id = await ig_api.reply_to_comment(
    comment_id=comments[0]["id"],
    message="Thanks for your comment!"
)

# Hide a comment
await ig_api.hide_comment(comment_id=comments[1]["id"], hide=True)

# Delete a comment
await ig_api.delete_comment(comment_id=comments[2]["id"])
```

### Getting Analytics

```python
# Account insights
insights = await ig_api.get_account_insights(
    ig_account_id="123456789",
    metrics=["impressions", "reach", "profile_views"],
    period="day"
)

# Post insights
post_insights = await ig_api.get_media_insights(
    media_id="987654321",
    metrics=["engagement", "impressions", "reach", "saved"]
)
```

## Error Handling

Common errors and solutions:

### 1. "No Instagram Business Account found"

**Cause:** User's Instagram account is not a Business/Creator account or not linked to a Facebook Page.

**Solution:**
- Convert Instagram account to Business/Creator
- Link Instagram to a Facebook Page
- Ensure user has admin access to both

### 2. "Invalid access token"

**Cause:** Access token expired or was revoked.

**Solution:**
- Implement token refresh logic
- Re-authenticate user
- Check token expiration in `accounts.token_expires_at`

### 3. "Video processing failed"

**Cause:** Video doesn't meet Instagram requirements.

**Solution:**
- Check video format (MP4 recommended)
- Verify aspect ratio (9:16, 1:1, or 4:5)
- Ensure duration is 3-60 seconds
- Reduce file size if over 100MB

### 4. "Rate limit exceeded"

**Cause:** Too many API requests in short time.

**Solution:**
- Implement exponential backoff
- Cache API responses
- Use webhooks for real-time updates
- Respect Instagram's rate limits

## Testing

### Local Testing

1. **Set up test Instagram account:**
   - Create Instagram Business account
   - Link to Facebook Page
   - Ensure you're admin of both

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Fill in INSTAGRAM_CLIENT_ID and INSTAGRAM_CLIENT_SECRET
   ```

3. **Run tests:**
   ```bash
   cd backend
   pytest tests/test_instagram_integration.py -v
   ```

### Manual Testing Checklist

- [ ] OAuth flow completes successfully
- [ ] Account information displays correctly
- [ ] Image post publishes to Instagram
- [ ] Video post publishes to Instagram
- [ ] Comments can be viewed and replied to
- [ ] Messages can be sent and received
- [ ] Analytics display correctly
- [ ] Account can be disconnected

## Security Considerations

1. **Token Encryption:**
   - All access tokens are encrypted with Fernet (AES-128)
   - Never log or display raw tokens
   - Tokens are stored encrypted in database

2. **OAuth State Validation:**
   - State tokens stored in Redis with 10-minute expiration
   - One-time use (deleted after validation)
   - Prevents CSRF attacks

3. **Access Control:**
   - Users can only access their own accounts
   - User ID validated on every request
   - Platform ownership checked before operations

4. **Data Privacy:**
   - Minimal data collection
   - Clear privacy policy
   - User can disconnect and delete data
   - Complies with Meta Platform Terms

## Monitoring

### Metrics to Track

- OAuth success/failure rates
- Publishing success/failure rates
- API error rates
- Token expiration events
- User engagement with features

### Logging

All Instagram API operations are logged with:
- User ID
- Action type
- Success/failure
- Error messages (if any)
- Timestamp

Example log entry:
```
[2025-11-10 12:34:56] INFO: Instagram publish started - user_id=123, post_id=456
[2025-11-10 12:35:42] INFO: Instagram publish success - user_id=123, post_id=456, media_id=789
```

## Troubleshooting

### Common Issues

1. **OAuth popup blocked:**
   - Enable popups for the domain
   - Use alternative OAuth flow (redirect-based)

2. **Video upload timeout:**
   - Implement background job for video processing
   - Use webhook for upload completion notification

3. **Permission denied:**
   - Check if permission is approved in App Review
   - Verify permission is in OAuth scope list
   - Re-authenticate user to get new permissions

## Resources

### Meta Documentation

- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Content Publishing](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [Comments](https://developers.facebook.com/docs/instagram-api/reference/ig-media/comments)
- [Insights](https://developers.facebook.com/docs/instagram-api/reference/ig-user/insights)
- [Messaging](https://developers.facebook.com/docs/messenger-platform/instagram)

### Internal Documentation

- [App Review Documentation](./meta-app-review/README.md)
- [Testing Guide](./meta-app-review/testing-guide.md)
- [Permission Use Cases](./meta-app-review/permission-use-cases.md)

## Future Enhancements

Potential improvements to the Instagram integration:

1. **Webhook Support:**
   - Real-time comment notifications
   - Message notifications
   - Insights updates

2. **Advanced Scheduling:**
   - Best time to post recommendations
   - Automatic rescheduling based on engagement
   - Multi-account posting

3. **Enhanced Analytics:**
   - Competitor analysis
   - Hashtag performance tracking
   - Audience demographics

4. **Content Optimization:**
   - Automatic hashtag suggestions
   - Caption optimization
   - Image enhancement filters

5. **Batch Operations:**
   - Bulk post scheduling
   - Bulk comment moderation
   - Batch export of analytics

## Support

For technical support or questions:

- **Developer:** ryanjulemcdowell@gmail.com
- **Documentation:** https://www.machine-systems.org/docs
- **Issues:** Create GitHub issue in repository

## License

This integration follows the Meta Platform Terms and Policies:
- https://developers.facebook.com/terms
- https://developers.facebook.com/policy
