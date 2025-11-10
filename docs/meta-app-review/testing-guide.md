# Meta App Review Testing Guide

This document provides step-by-step instructions for Meta app reviewers to test Content Clipper's Instagram integration.

## Prerequisites

Before testing, please ensure you have:

1. ✅ Test credentials (provided in app review submission)
2. ✅ An Instagram Business Account connected to a Facebook Page
3. ✅ At least one test video/image file to upload
4. ✅ Modern web browser (Chrome, Firefox, Safari, or Edge)

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Testing: Account Connection (pages_show_list, public_profile)](#test-1-account-connection)
3. [Testing: Profile Display (instagram_business_basic)](#test-2-profile-display)
4. [Testing: Content Publishing (instagram_business_content_publish)](#test-3-content-publishing)
5. [Testing: Comment Management (instagram_manage_comments)](#test-4-comment-management)
6. [Testing: Message Management (instagram_business_manage_messages)](#test-5-message-management)
7. [Testing: Analytics (instagram_business_manage_insights, pages_read_engagement)](#test-6-analytics)
8. [Testing: Account Disconnection](#test-7-account-disconnection)
9. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Step 1: Access the Application

1. Navigate to: **https://www.machine-systems.org**
2. Log in using the provided test credentials:
   - Email: `[provided in submission]`
   - Password: `[provided in submission]`

### Step 2: Navigate to Accounts Page

1. After logging in, click **"Accounts"** in the main navigation menu
2. You should see the Accounts management page with options to connect social media accounts

---

## Test 1: Account Connection

**Permissions Tested:** `pages_show_list`, `public_profile`, `instagram_basic`, `instagram_business_basic`, `business_management`

### Steps

1. On the Accounts page, click **"Connect Account"** button
2. Select **"Instagram"** from the platform options
3. A popup window will open with Facebook Login
4. Log in with your Facebook account (or use the test account provided)
5. Review the permissions requested:
   - ✅ All 11 permissions should be listed
   - ✅ Each permission should have a clear description
6. Click **"Continue"** to authorize
7. If you manage multiple Facebook Pages, select the Page connected to your Instagram Business account
8. The popup should close automatically
9. You should see a success message

### Expected Results

✅ Instagram account appears in the connected accounts list
✅ Account shows the correct Instagram username
✅ Profile picture is displayed
✅ Account status shows as "Active"
✅ Connection timestamp is shown

### What This Tests

- `pages_show_list`: Lists your Facebook Pages with Instagram accounts
- `public_profile`: Retrieves your Facebook profile info for authentication
- `instagram_business_basic`: Gets Instagram Business account details
- `business_management`: Accesses business-owned Instagram accounts

### Screenshots

Take screenshots showing:
- The OAuth permission dialog
- Successfully connected Instagram account in the accounts list

---

## Test 2: Profile Display

**Permissions Tested:** `instagram_business_basic`

### Steps

1. On the Accounts page, locate your connected Instagram account
2. Click on the account card to view details
3. Verify the following information is displayed:
   - ✅ Instagram username
   - ✅ Display name
   - ✅ Profile picture
   - ✅ Follower count
   - ✅ Following count
   - ✅ Media count (number of posts)

### Expected Results

✅ All account information is accurate and matches your Instagram profile
✅ Profile picture loads correctly
✅ Follower/following counts are current

### What This Tests

- `instagram_business_basic`: Retrieves comprehensive profile information

### Screenshots

Take screenshots showing the account profile details.

---

## Test 3: Content Publishing

**Permissions Tested:** `instagram_business_content_publish`

This is the **primary feature** of Content Clipper.

### Part A: Upload Content

1. Navigate to **"Content Library"** or **"Clips"** in the main menu
2. Click **"Upload Clip"** or **"New Clip"**
3. Upload a test video file (MP4, MOV, or similar)
   - **Note:** For app review, you can use a short test video (10-30 seconds)
   - Instagram requires videos to be at least 3 seconds long
4. Wait for upload to complete
5. Add a title to the clip
6. Click **"Save"**

### Part B: Create Scheduled Post

1. Navigate to **"Social Scheduler"** in the main menu
2. Click **"Create Post"** or **"New Post"**
3. Fill in the post details:
   - **Platform:** Select "Instagram"
   - **Clip:** Select the clip you just uploaded
   - **Caption:** Enter test caption (e.g., "Testing Content Clipper scheduling! 🚀")
   - **Hashtags:** Add test hashtags (e.g., "#contentcreator #socialmedia #test")
   - **Schedule Time:** Select "Publish Now" or choose a time in the next few minutes
4. Click **"Create Post"** or **"Schedule Post"**

### Part C: Verify Publishing

1. If you selected "Publish Now":
   - Wait for the publishing process to complete (15-60 seconds for videos)
   - You should see a progress indicator
   - Once complete, you should see a success message
   - A link to the Instagram post should be displayed
2. If you scheduled for later:
   - The post should appear in the scheduled posts list
   - Status should show as "Scheduled"
   - At the scheduled time, the status should change to "Publishing" then "Published"

### Part D: Verify on Instagram

1. Open Instagram in a new tab or on your mobile device
2. Navigate to your Instagram Business account profile
3. Verify the post appears in your feed with:
   - ✅ Correct video content
   - ✅ Correct caption
   - ✅ Correct hashtags

### Expected Results

✅ Video uploads successfully to Content Clipper
✅ Post can be created with all details
✅ Scheduled posts appear in the calendar/list
✅ Publishing process completes without errors
✅ Post appears on Instagram with correct content
✅ Link to Instagram post works correctly

### What This Tests

- `instagram_business_content_publish`: Full content publishing workflow
  - Creating media containers
  - Uploading video content
  - Publishing to Instagram
  - Video processing status checking

### Screenshots

Take screenshots showing:
- The create post form filled out
- Publishing in progress
- Successfully published post in Content Clipper
- The published post on Instagram

---

## Test 4: Comment Management

**Permissions Tested:** `instagram_manage_comments`

### Part A: View Comments

1. On the Instagram post you just published, add a test comment using your Instagram account or another test account
2. In Content Clipper, navigate to the post details or comments section
3. Click **"View Comments"** or refresh the post

### Part B: Reply to Comment

1. Locate the test comment in Content Clipper
2. Click **"Reply"** button next to the comment
3. Enter a test reply (e.g., "Thanks for your comment!")
4. Click **"Send Reply"**
5. Verify the reply appears in Content Clipper
6. Check Instagram to confirm the reply appears there as well

### Part C: Hide Comment (Optional)

1. In Content Clipper, locate a comment
2. Click **"Hide"** or **"Moderate"** button
3. The comment should be hidden on Instagram
4. Click **"Unhide"** to restore it

### Part D: Delete Comment (Optional)

1. Add another test comment on Instagram
2. In Content Clipper, click **"Delete"** on the test comment
3. Confirm deletion
4. Verify the comment is removed from both Content Clipper and Instagram

### Expected Results

✅ Comments from Instagram appear in Content Clipper
✅ Replies can be sent and appear on Instagram
✅ Comments can be hidden/unhidden
✅ Comments can be deleted
✅ Comment count updates correctly

### What This Tests

- `instagram_manage_comments`: Complete comment management workflow
  - Reading comments
  - Replying to comments
  - Hiding comments
  - Deleting comments

### Screenshots

Take screenshots showing:
- Comments list in Content Clipper
- Replying to a comment
- The reply appearing on Instagram

---

## Test 5: Message Management

**Permissions Tested:** `instagram_business_manage_messages`, `instagram_manage_messages`

### Part A: View Messages

1. Send a test Direct Message to your Instagram Business account from another Instagram account
2. In Content Clipper, navigate to **"Messages"** or **"Inbox"**
3. Click on your Instagram account to view messages

### Part B: Reply to Message

1. Locate the test message in Content Clipper
2. Click on the conversation to open it
3. Type a reply message (e.g., "Hello! Thanks for reaching out.")
4. Click **"Send"**
5. Verify the reply appears in Content Clipper
6. Check Instagram to confirm the message was sent

### Part C: View Message History

1. In Content Clipper, scroll through the conversation
2. Verify that the full message history is displayed

### Expected Results

✅ Incoming messages appear in Content Clipper inbox
✅ Conversation threads are displayed correctly
✅ Replies can be sent from Content Clipper
✅ Messages appear on Instagram in real-time
✅ Message history is preserved

### What This Tests

- `instagram_business_manage_messages`: Message management workflow
  - Viewing conversations
  - Reading messages
  - Sending replies
  - Managing customer support

### Screenshots

Take screenshots showing:
- Messages inbox with conversations
- Individual conversation thread
- Sending a reply

---

## Test 6: Analytics

**Permissions Tested:** `instagram_business_manage_insights`, `pages_read_engagement`

### Part A: Account-Level Insights

1. Navigate to **"Analytics"** or **"Insights"** in the main menu
2. Select your Instagram account
3. View the following metrics:
   - ✅ Impressions
   - ✅ Reach
   - ✅ Profile views
   - ✅ Follower count over time
   - ✅ Engagement rate

### Part B: Post-Level Insights

1. Navigate to a published post
2. Click **"View Insights"** or **"Analytics"**
3. View the following metrics:
   - ✅ Impressions
   - ✅ Reach
   - ✅ Engagement (likes + comments + saves)
   - ✅ Saves
   - ✅ Shares (if available)
   - ✅ Video views (for video posts)

### Part C: Page Insights (Optional)

1. If available, view Facebook Page insights for the linked Page
2. Verify cross-platform analytics are displayed

### Expected Results

✅ Account insights display correctly
✅ Metrics match Instagram's native analytics
✅ Post insights show detailed performance data
✅ Charts and graphs render properly
✅ Date ranges can be adjusted

### What This Tests

- `instagram_business_manage_insights`: Analytics and performance data
  - Account-level metrics
  - Post-level metrics
  - Historical data
- `pages_read_engagement`: Facebook Page engagement metrics

### Screenshots

Take screenshots showing:
- Analytics dashboard with account metrics
- Individual post insights
- Charts/graphs displaying performance over time

---

## Test 7: Account Disconnection

**Testing Data Deletion and Account Management**

### Steps

1. Navigate to **"Accounts"** page
2. Locate your connected Instagram account
3. Click **"Disconnect"** or **"Remove Account"**
4. Confirm the disconnection when prompted
5. The Instagram account should be removed from the connected accounts list

### Expected Results

✅ Account is removed from Content Clipper
✅ Access tokens are deleted from database
✅ User data associated with the account is marked for deletion
✅ User can reconnect the account if desired

### What This Tests

- Account disconnection workflow
- Data deletion compliance
- User control over connected accounts

### Screenshots

Take screenshots showing:
- Confirmation dialog for disconnection
- Accounts list after disconnection

---

## Test 8: Reconnection (Optional)

### Steps

1. After disconnecting, click **"Connect Account"** again
2. Follow the OAuth flow to reconnect your Instagram account
3. Verify all features work as before

### Expected Results

✅ Account reconnects successfully
✅ All permissions are re-granted
✅ Previous posts and data are accessible (if not deleted)

---

## Troubleshooting

### Issue: OAuth popup is blocked

**Solution:** Enable popups for machine-systems.org in your browser settings

### Issue: "No Instagram Business Account found"

**Solution:** Ensure your Instagram account is converted to a Business or Creator account and linked to a Facebook Page

### Issue: Video publishing fails

**Solution:**
- Verify video file is in a supported format (MP4, MOV)
- Ensure video meets Instagram requirements:
  - At least 3 seconds long
  - Aspect ratio between 4:5 and 16:9
  - Maximum file size: 100MB
  - Maximum duration: 60 seconds (for feed), 90 seconds (for reels)

### Issue: Permissions not granted

**Solution:** During OAuth, ensure all permissions are accepted. If any are denied, disconnect and reconnect the account with all permissions granted.

### Issue: Analytics not showing

**Solution:** Instagram Insights require:
- Business or Creator account
- At least 100 followers (for some metrics)
- 24-48 hours of data collection for new accounts

---

## Test Summary Checklist

Use this checklist to ensure all features have been tested:

- [ ] **Account Connection**
  - [ ] OAuth flow completes successfully
  - [ ] All permissions are requested
  - [ ] Instagram account appears in connected accounts

- [ ] **Profile Display**
  - [ ] Username, name, and profile picture display
  - [ ] Follower/following counts are correct

- [ ] **Content Publishing**
  - [ ] Can upload video content
  - [ ] Can create scheduled post
  - [ ] Post publishes to Instagram successfully
  - [ ] Published post appears on Instagram with correct content

- [ ] **Comment Management**
  - [ ] Can view comments on posts
  - [ ] Can reply to comments
  - [ ] Can hide/unhide comments
  - [ ] Can delete comments

- [ ] **Message Management**
  - [ ] Can view incoming messages
  - [ ] Can read conversation history
  - [ ] Can send replies
  - [ ] Messages appear on Instagram

- [ ] **Analytics**
  - [ ] Account-level insights display
  - [ ] Post-level insights display
  - [ ] Metrics are accurate

- [ ] **Account Management**
  - [ ] Can disconnect account
  - [ ] Can reconnect account

---

## Support During Review

If you encounter any issues during testing, please contact:

**Email:** ryanjulemcdowell@gmail.com
**Subject:** Meta App Review - Content Clipper Testing Issue

We typically respond within 2-4 hours during business hours (9 AM - 6 PM EST).

---

## Additional Notes

- All features are live and functional on the production environment
- Test credentials are valid for 30 days from submission date
- The application follows Meta's Platform Terms and Policies
- User data is encrypted and stored securely
- Privacy Policy and Terms of Service are available on the website

Thank you for reviewing Content Clipper!
