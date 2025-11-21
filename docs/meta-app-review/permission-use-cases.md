# Permission Use Cases

This document describes exactly how Content Clipper uses each requested permission.

## Table of Contents

1. [public_profile](#public_profile)
2. [pages_show_list](#pages_show_list)
3. [instagram_basic](#instagram_basic)
4. [instagram_business_basic](#instagram_business_basic)
5. [instagram_business_content_publish](#instagram_business_content_publish)
6. [instagram_manage_comments](#instagram_manage_comments)
7. [instagram_manage_messages](#instagram_manage_messages)
8. [instagram_business_manage_messages](#instagram_business_manage_messages)
9. [instagram_business_manage_insights](#instagram_business_manage_insights)
10. [pages_read_engagement](#pages_read_engagement)
11. [business_management](#business_management)

---

## public_profile

**Permission Type:** Facebook Basic Permission
**Required:** Yes
**API Endpoints Used:** `/me`

### Use Case

This permission is required to identify the Facebook user during the OAuth login process. We use it to:

1. Display the user's name in the account connection interface
2. Link the Facebook account to their Content Clipper profile
3. Verify the user's identity during authentication

### Implementation

**File:** `backend/app/services/oauth_service.py` (lines 132-138)

```python
# Get Facebook user ID
me_response = await client.get(
    f"https://graph.facebook.com/v18.0/me?access_token={access_token}"
)
me_response.raise_for_status()
fb_user = me_response.json()
```

### User Benefit

Users can securely connect their Instagram Business account through Facebook authentication.

---

## pages_show_list

**Permission Type:** Facebook Pages Permission
**Required:** Yes
**API Endpoints Used:** `/me/accounts`

### Use Case

Instagram Business accounts must be linked to a Facebook Page. This permission allows us to:

1. List all Facebook Pages the user manages
2. Identify which Pages have connected Instagram Business accounts
3. Allow users to select which Instagram account to connect

### Implementation

**File:** `backend/app/services/oauth_service.py` (lines 140-149)

```python
# Get pages managed by this user
pages_response = await client.get(
    f"https://graph.facebook.com/v18.0/me/accounts",
    params={
        "fields": "id,name,instagram_business_account,access_token",
        "access_token": access_token
    }
)
```

**File:** `backend/app/services/instagram_graph_service.py` (lines 65-79)

```python
async def get_facebook_pages(self, user_id: str = "me") -> List[Dict[str, Any]]:
    """
    Get list of Facebook Pages the user manages.
    Permission: pages_show_list
    """
```

### User Benefit

Users can see all their Facebook Pages and choose which Instagram Business account to connect to Content Clipper.

### Screenshots

- `screenshots/page-selection.png` - Shows list of available Pages with Instagram accounts

---

## instagram_basic

**Permission Type:** Instagram Basic Permission
**Required:** Yes (for non-Business accounts)
**API Endpoints Used:** `/me`

### Use Case

Provides basic access to Instagram accounts. Used as a fallback or for Creator accounts that aren't Business accounts.

### Implementation

**File:** `backend/app/services/oauth_service.py` (lines 92-104)

Requested as part of the scope array but primarily `instagram_business_basic` is used for Business accounts.

### User Benefit

Ensures compatibility with both Business and Creator accounts.

---

## instagram_business_basic

**Permission Type:** Instagram Business Permission
**Required:** Yes
**API Endpoints Used:** `/{ig-user-id}`

### Use Case

This permission allows us to retrieve and display basic Instagram Business Account information:

1. Username and display name
2. Profile picture
3. Follower/following counts
4. Biography and website
5. Media count

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 83-108)

```python
async def get_instagram_account_info(self, ig_account_id: str) -> Dict[str, Any]:
    """
    Get Instagram Business Account information.
    Permission: instagram_business_basic
    Use case: Display account details and verify connection
    """
    params = {
        "fields": "id,username,name,profile_picture_url,followers_count,follows_count,media_count,website,biography"
    }
    return await self._make_request("GET", ig_account_id, params=params)
```

### User Benefit

Users can:
- Verify the correct account is connected
- See their profile information in the dashboard
- Monitor follower growth over time

### Screenshots

- `screenshots/account-dashboard.png` - Shows connected Instagram account info
- `screenshots/account-profile.png` - Displays profile details

---

## instagram_business_content_publish

**Permission Type:** Instagram Business Permission
**Required:** Yes (Core Feature)
**API Endpoints Used:**
- `/{ig-user-id}/media` (POST)
- `/{ig-user-id}/media_publish` (POST)
- `/{container-id}` (GET - status check)

### Use Case

This is our **primary permission** and enables the core functionality of Content Clipper. It allows users to:

1. Upload and publish image posts to Instagram
2. Upload and publish video posts (Reels)
3. Create carousel posts with multiple images/videos
4. Publish Instagram Stories
5. Schedule content for future publishing

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 110-310)

#### Image Publishing
```python
async def create_image_container(
    self,
    ig_account_id: str,
    image_url: str,
    caption: Optional[str] = None,
    location_id: Optional[str] = None,
    user_tags: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a media container for a single image.
    Permission: instagram_business_content_publish
    Use case: Publish images to Instagram from scheduled posts
    """
```

#### Video/Reel Publishing
```python
async def create_video_container(
    self,
    ig_account_id: str,
    video_url: str,
    caption: Optional[str] = None,
    location_id: Optional[str] = None,
    thumb_offset: Optional[int] = None,
    media_type: str = "REELS"
) -> str:
    """
    Create a media container for a video or reel.
    Permission: instagram_business_content_publish
    Use case: Publish videos and reels to Instagram from scheduled posts
    """
```

#### Publishing Flow
```python
async def publish_container(self, ig_account_id: str, creation_id: str) -> str:
    """
    Publish a media container.
    Permission: instagram_business_content_publish
    Use case: Finalize and publish scheduled content
    """
```

**File:** `backend/app/services/social_service.py` (lines 175-283)

Complete implementation of Instagram publishing workflow with video status checking and error handling.

### User Benefit

Users can:
- Schedule posts in advance for optimal posting times
- Maintain a consistent posting schedule
- Publish content automatically without manual intervention
- Post videos and Reels directly from their content library

### User Flow

1. User uploads a video clip to Content Clipper
2. User creates a post with caption and hashtags
3. User schedules the post for a specific date/time
4. At scheduled time, Content Clipper automatically publishes to Instagram
5. User receives confirmation with link to published post

### Screenshots

- `screenshots/create-post.png` - Creating a scheduled post
- `screenshots/schedule-calendar.png` - Calendar view of scheduled posts
- `screenshots/publishing-progress.png` - Post being published
- `screenshots/published-success.png` - Successfully published post

---

## instagram_manage_comments

**Permission Type:** Instagram Permission
**Required:** Yes
**API Endpoints Used:**
- `/{media-id}/comments` (GET)
- `/{comment-id}/replies` (POST)
- `/{comment-id}` (DELETE, POST - hide)

### Use Case

This permission enables community engagement features:

1. Read comments on published posts
2. Reply to user comments
3. Delete inappropriate comments
4. Hide spam or offensive comments
5. View comment replies and threads

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 312-391)

#### View Comments
```python
async def get_media_comments(
    self,
    media_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get comments on a media object.
    Permission: instagram_manage_comments
    Use case: Display and moderate comments on published posts
    """
```

#### Reply to Comments
```python
async def reply_to_comment(
    self,
    comment_id: str,
    message: str
) -> str:
    """
    Reply to a comment.
    Permission: instagram_manage_comments
    Use case: Respond to user comments for engagement
    """
```

#### Moderate Comments
```python
async def delete_comment(self, comment_id: str) -> bool:
    """
    Delete a comment.
    Permission: instagram_manage_comments
    Use case: Moderate inappropriate comments
    """

async def hide_comment(self, comment_id: str, hide: bool = True) -> bool:
    """
    Hide or unhide a comment.
    Permission: instagram_manage_comments
    Use case: Moderate comments without deleting them
    """
```

### User Benefit

Users can:
- Engage with their audience by replying to comments
- Maintain a positive community by moderating inappropriate content
- View all comments in one centralized dashboard
- Respond faster to customer questions and feedback

### Screenshots

- `screenshots/comments-list.png` - List of comments on posts
- `screenshots/comment-reply.png` - Replying to a comment
- `screenshots/comment-moderation.png` - Hiding/deleting comments

---

## instagram_manage_messages

**Permission Type:** Instagram Permission (Legacy)
**Required:** Yes
**API Endpoints Used:** Various message endpoints

### Use Case

Legacy permission for managing Instagram Direct messages. Works in conjunction with `instagram_business_manage_messages` to ensure compatibility across different account types.

### Implementation

Included in scope for backwards compatibility and comprehensive message access.

### User Benefit

Ensures full message access across all Instagram account types.

---

## instagram_business_manage_messages

**Permission Type:** Instagram Business Permission
**Required:** Yes
**API Endpoints Used:**
- `/{ig-user-id}/conversations` (GET)
- `/{conversation-id}/messages` (GET)
- `/{ig-user-id}/messages` (POST)

### Use Case

This permission enables customer support and engagement through Instagram Direct Messages:

1. View incoming direct messages
2. Send replies to customer inquiries
3. Manage conversation threads
4. View message history

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 393-461)

#### View Conversations
```python
async def get_conversations(
    self,
    ig_account_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get Instagram Direct message conversations.
    Permission: instagram_business_manage_messages
    Use case: Display user messages for customer support
    """
```

#### View Messages
```python
async def get_conversation_messages(
    self,
    conversation_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get messages in a conversation.
    Permission: instagram_business_manage_messages
    Use case: View message history for customer support
    """
```

#### Send Messages
```python
async def send_message(
    self,
    ig_account_id: str,
    recipient_id: str,
    message: str
) -> str:
    """
    Send a direct message.
    Permission: instagram_business_manage_messages
    Use case: Reply to customer inquiries
    """
```

### User Benefit

Users can:
- Respond to customer inquiries from Content Clipper dashboard
- Manage all messages in one place
- Provide better customer service
- Track conversation history

### Screenshots

- `screenshots/messages-inbox.png` - Inbox showing conversations
- `screenshots/message-thread.png` - Individual conversation thread
- `screenshots/send-message.png` - Sending a reply

---

## instagram_business_manage_insights

**Permission Type:** Instagram Business Permission
**Required:** Yes
**API Endpoints Used:**
- `/{ig-user-id}/insights` (GET)
- `/{media-id}/insights` (GET)

### Use Case

This permission provides analytics and performance data:

1. Account-level metrics (impressions, reach, profile views)
2. Post-level metrics (engagement, likes, comments, saves)
3. Story metrics (impressions, replies, exits)
4. Audience demographics and growth
5. Performance over time

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 463-539)

#### Account Insights
```python
async def get_account_insights(
    self,
    ig_account_id: str,
    metrics: List[str],
    period: str = "day",
    since: Optional[int] = None,
    until: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get account-level insights.
    Permission: instagram_business_manage_insights
    Use case: Display analytics dashboard for account performance

    Metrics examples: ["impressions", "reach", "profile_views",
                       "follower_count", "email_contacts", "phone_call_clicks"]
    """
```

#### Media Insights
```python
async def get_media_insights(
    self,
    media_id: str,
    metrics: List[str]
) -> List[Dict[str, Any]]:
    """
    Get insights for a specific media object.
    Permission: instagram_business_manage_insights
    Use case: Display performance metrics for individual posts

    Metrics examples: ["engagement", "impressions", "reach", "saved",
                       "video_views", "likes", "comments"]
    """
```

#### Story Insights
```python
async def get_story_insights(
    self,
    media_id: str,
    metrics: List[str]
) -> List[Dict[str, Any]]:
    """
    Get insights for a story.
    Permission: instagram_business_manage_insights
    Use case: Track story performance metrics

    Metrics examples: ["impressions", "reach", "replies", "exits", "taps_forward", "taps_back"]
    """
```

### User Benefit

Users can:
- Track the performance of their posts and stories
- Understand which content resonates with their audience
- Make data-driven decisions about content strategy
- Monitor account growth and engagement trends
- Optimize posting times based on audience activity

### Screenshots

- `screenshots/analytics-dashboard.png` - Overview of account analytics
- `screenshots/post-insights.png` - Individual post performance
- `screenshots/growth-metrics.png` - Follower growth over time

---

## pages_read_engagement

**Permission Type:** Facebook Pages Permission
**Required:** Yes
**API Endpoints Used:** `/{page-id}/insights` (GET)

### Use Case

Since Instagram Business accounts are linked to Facebook Pages, this permission allows us to:

1. Read engagement metrics for the linked Facebook Page
2. Provide comprehensive cross-platform analytics
3. Show how Facebook Page activity correlates with Instagram performance

### Implementation

**File:** `backend/app/services/instagram_graph_service.py` (lines 541-572)

```python
async def get_page_insights(
    self,
    page_id: str,
    metrics: List[str],
    period: str = "day",
    since: Optional[str] = None,
    until: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get Facebook Page engagement insights.
    Permission: pages_read_engagement
    Use case: Display Facebook Page analytics for linked Instagram accounts

    Metrics examples: ["page_impressions", "page_engaged_users",
                       "page_post_engagements", "page_fans"]
    """
```

### User Benefit

Users get a complete picture of their social media performance across both Instagram and Facebook.

### Screenshots

- `screenshots/page-analytics.png` - Facebook Page engagement metrics

---

## business_management

**Permission Type:** Business Permission
**Required:** Yes
**API Endpoints Used:** Various business asset endpoints

### Use Case

This permission allows management of business assets:

1. Access to business-owned Instagram accounts
2. Manage multiple Instagram accounts under one business
3. Business-level permissions and access control
4. Required for enterprise and agency features

### Implementation

This permission is requested to ensure:
- Proper access to business-owned Instagram accounts
- Support for business users managing multiple accounts
- Compliance with business account requirements
- Future support for business manager features

### User Benefit

Businesses and agencies can:
- Manage multiple client accounts
- Maintain proper business account access
- Use Content Clipper for commercial purposes
- Scale their social media management

---

## Summary

All permissions are used to provide a comprehensive social media management platform that allows users to:

1. **Publish Content** - Schedule and automatically post to Instagram
2. **Engage with Audience** - Respond to comments and messages
3. **Track Performance** - View detailed analytics and insights
4. **Manage Accounts** - Connect and manage multiple Instagram Business accounts
5. **Optimize Strategy** - Make data-driven decisions based on performance metrics

Each permission is essential to the core functionality of Content Clipper and provides direct value to end users.
