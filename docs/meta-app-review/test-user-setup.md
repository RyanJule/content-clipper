# Test User Setup Guide

This document explains how to set up test credentials for Meta app review.

## Overview

Meta requires functional test credentials to verify that all requested permissions work correctly. This guide covers:

1. Setting up a test Instagram Business account
2. Configuring a test Facebook Page
3. Preparing test content
4. Creating test user accounts in Content Clipper

---

## Prerequisites

Before submitting for app review, you need:

- ✅ A Facebook Page (for linking Instagram Business account)
- ✅ An Instagram Business or Creator account
- ✅ The Instagram account linked to the Facebook Page
- ✅ Admin access to both accounts
- ✅ Test video content for publishing

---

## Step 1: Create/Configure Facebook Page

### Option A: Use Existing Facebook Page

If you already have a Facebook Page:

1. Ensure you have admin access
2. Verify the Page has an Instagram Business account connected
3. Note the Page name and ID

### Option B: Create New Test Page

1. Go to [facebook.com/pages/create](https://www.facebook.com/pages/create)
2. Choose a page type: "Business or Brand"
3. Enter details:
   - **Page Name:** "Content Clipper Test Page"
   - **Category:** "Software Company" or "Social Media Company"
   - **Description:** "Test page for Content Clipper app review"
4. Click **"Create Page"**
5. Upload a profile picture and cover photo (optional)

---

## Step 2: Create/Configure Instagram Business Account

### Option A: Use Existing Instagram Business Account

If you already have an Instagram Business account:

1. Ensure it's connected to your Facebook Page
2. Verify you have admin access
3. Note the Instagram username

### Option B: Create New Test Account

1. Download Instagram mobile app
2. Create new Instagram account:
   - **Username:** Choose a test username (e.g., "contentclipper_test")
   - **Email:** Use a test email address
   - **Password:** Use a strong password (save it for app review submission)
3. Convert to Business Account:
   - Go to **Settings → Account**
   - Tap **"Switch to Professional Account"**
   - Choose **"Business"**
   - Select a category (e.g., "App" or "Software")
   - Tap **"Done"**
4. Connect to Facebook Page:
   - Go to **Settings → Account → Linked Accounts**
   - Tap **"Facebook"**
   - Log in to Facebook
   - Select your Facebook Page
   - Confirm connection

### Verify Connection

1. Go to your Facebook Page settings
2. Navigate to **Instagram → Connected Account**
3. Verify your Instagram Business account is listed

---

## Step 3: Prepare Test Content

Create or gather test content for publishing:

### Test Videos

Prepare 2-3 short test videos:

**Requirements:**
- Format: MP4 or MOV
- Duration: 10-60 seconds (optimal for testing)
- Aspect ratio: 9:16 (vertical) or 1:1 (square)
- Resolution: At least 720p
- Content: Non-copyrighted, appropriate content

**Suggestions:**
- Screen recording of app features
- Simple animated graphics
- Stock footage (with proper licenses)
- Original video content

**Where to get test videos:**
- [Pexels](https://www.pexels.com/videos/) - Free stock videos
- [Pixabay](https://pixabay.com/videos/) - Free stock videos
- Create simple screen recordings

### Test Images (Optional)

For carousel or image post testing:
- Format: JPG or PNG
- Aspect ratio: 1:1 (square) or 4:5 (portrait)
- Resolution: At least 1080x1080px

---

## Step 4: Create Content Clipper Test User

### Register Test Account

1. Go to **https://www.machine-systems.org**
2. Click **"Sign Up"** or **"Register"**
3. Fill in registration details:
   - **Email:** Use a test email (e.g., `contentclipper.test@gmail.com`)
   - **Password:** Create a strong password
   - **Full Name:** "Test User" or "App Review Test"
4. Verify email address (check inbox for verification email)
5. Complete profile setup

### Document Credentials

**IMPORTANT:** Document these credentials for the app review submission form:

```
Content Clipper Login:
- URL: https://www.machine-systems.org
- Email: [your test email]
- Password: [your test password]

Instagram Account:
- Username: [your Instagram username]
- Password: [your Instagram password]

Facebook Account:
- Email: [Facebook login email]
- Password: [Facebook password]

Facebook Page:
- Page Name: [your Page name]
- Page URL: [Facebook Page URL]
```

**Security Note:** Use passwords you're comfortable sharing with Meta reviewers. Don't use personal account passwords.

---

## Step 5: Connect Instagram Account in Content Clipper

Before submitting for app review, verify the connection works:

1. Log in to Content Clipper with your test account
2. Navigate to **"Accounts"** page
3. Click **"Connect Account"**
4. Select **"Instagram"**
5. Complete OAuth flow:
   - Log in with Facebook
   - Grant all requested permissions
   - Select your Facebook Page
6. Verify account appears as connected

### Troubleshooting Connection Issues

**Issue:** "No Instagram Business Account found"
- **Solution:** Ensure Instagram account is set to Business/Creator and linked to Facebook Page

**Issue:** OAuth fails or shows error
- **Solution:** Check that:
  - Facebook app ID and secret are correctly configured
  - Redirect URI is whitelisted in Facebook App settings
  - All required permissions are enabled in App Review settings

---

## Step 6: Test Core Functionality

Before submitting, test that everything works:

### Test 1: Upload Content

1. Upload a test video to Content Clipper
2. Verify upload completes successfully
3. Video should appear in Clips/Content Library

### Test 2: Create and Publish Post

1. Create a new scheduled post
2. Select Instagram platform
3. Choose your test video
4. Add caption and hashtags
5. Select "Publish Now"
6. Wait for publishing to complete (30-60 seconds)
7. Verify post appears on Instagram

### Test 3: Verify All Features

Test the following features work:
- [ ] Account connection
- [ ] Profile information display
- [ ] Content publishing
- [ ] Comments (add a test comment on Instagram, view in Content Clipper)
- [ ] Messages (send a test DM, view in Content Clipper)
- [ ] Analytics (verify insights appear)

If any feature doesn't work, debug before submitting for app review.

---

## Step 7: Prepare App Review Submission

### Information to Provide Meta

When submitting for app review, you'll need to provide:

1. **Test User Credentials** (from Step 4)
2. **Detailed Testing Instructions** (see testing-guide.md)
3. **Demo Video** (see demo-video-script.md)
4. **Permission Justifications** (see permission-use-cases.md)
5. **Privacy Policy URL:** https://www.machine-systems.org/privacy-policy
6. **Terms of Service URL:** https://www.machine-systems.org/terms-of-service
7. **App Icon/Logo**
8. **Screenshots** of each feature

### App Review Checklist

Before submitting:

- [ ] Test account is created and verified
- [ ] Instagram Business account is connected to Facebook Page
- [ ] All permissions are working in production
- [ ] Test credentials are documented
- [ ] Demo video is recorded
- [ ] Screenshots are captured
- [ ] Privacy Policy is accessible
- [ ] Terms of Service is accessible
- [ ] Support email is monitored
- [ ] All features are functional

---

## Maintaining Test Accounts

### During Review

- **Monitor test account:** Check daily for messages from Meta reviewers
- **Keep content live:** Don't delete test posts during review
- **Respond quickly:** Reply to any reviewer questions within 24 hours
- **Keep credentials valid:** Ensure passwords don't expire

### After Approval

- **Keep test account active:** Meta may re-review periodically
- **Update if changes:** If you modify permissions or features, update test scenarios
- **Maintain documentation:** Keep all documentation current

### If Review is Rejected

- **Read feedback carefully:** Meta provides specific reasons for rejection
- **Fix issues:** Address all concerns raised
- **Update documentation:** Revise use case descriptions if needed
- **Resubmit:** Follow the resubmission process

---

## Best Practices

### For Test Accounts

1. **Use realistic data:** Create test content that represents actual use cases
2. **Keep accounts active:** Post occasionally to prevent account flags
3. **Follow platform rules:** Ensure test content complies with Instagram policies
4. **Document everything:** Keep detailed records of test account setup

### For App Review

1. **Be thorough:** Test every permission before submitting
2. **Be responsive:** Monitor email for reviewer questions
3. **Be patient:** Review can take 3-7 days (sometimes longer)
4. **Be prepared:** Have backup plans if initial submission is rejected

---

## Common Issues and Solutions

### Issue: Instagram account can't be converted to Business

**Cause:** Account doesn't meet minimum requirements
**Solution:**
- Add profile photo
- Post at least 3-5 pieces of content
- Add bio and website
- Wait 24 hours and try again

### Issue: Can't connect Instagram to Facebook Page

**Cause:** Account connection restrictions
**Solution:**
- Ensure you're admin of both Page and Instagram account
- Use Instagram mobile app to connect (not desktop)
- Disconnect any existing Page connections first
- Clear Instagram app cache and try again

### Issue: Permissions are denied during OAuth

**Cause:** User declined permissions
**Solution:**
- Disconnect account
- Reconnect and accept all permissions
- If specific permission is blocked, check why in Facebook Business Suite

### Issue: Video publishing fails

**Cause:** Video doesn't meet Instagram requirements
**Solution:**
- Check video format (use MP4)
- Verify aspect ratio (9:16, 1:1, or 4:5)
- Ensure video is 3-60 seconds
- Reduce file size if over 100MB
- Check that video URL is publicly accessible

---

## Security Considerations

### Protecting Test Credentials

1. **Use dedicated test accounts:** Never use personal accounts
2. **Use unique passwords:** Don't reuse passwords from other services
3. **Rotate after review:** Change passwords after app review completes
4. **Limit access:** Only share with necessary team members

### Data Privacy

1. **Use test data only:** Don't use real customer data
2. **Clear after review:** Delete test content after approval
3. **Monitor access:** Review account activity logs regularly
4. **Revoke when done:** Disconnect test accounts when no longer needed

---

## Resources

### Meta Documentation

- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api/)
- [App Review Process](https://developers.facebook.com/docs/app-review/)
- [Business Account Setup](https://www.facebook.com/business/help/1492627900875762)

### Content Clipper Support

- **Email:** ryanjulemcdowell@gmail.com
- **Support:** support@contentclipper.com
- **Documentation:** https://www.machine-systems.org/docs

---

## Questions?

If you have questions about setting up test accounts or the app review process, please contact:

**Email:** ryanjulemcdowell@gmail.com
**Subject:** Meta App Review - Test Setup Question

We're here to help ensure a smooth review process!
