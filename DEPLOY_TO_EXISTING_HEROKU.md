# Deploy Ultra Bot to Your Existing Heroku App

## Prerequisites
- Heroku CLI installed and logged in
- Your existing Heroku app name (from previous deployment)

## Step 1: Download Deployment Package
Download `ultra_bot_heroku_deployment.zip` to your local machine and extract it.

## Step 2: Navigate to Deployment Folder
```bash
cd heroku_deployment
```

## Step 3: Connect to Your Existing Heroku App
Replace `your-existing-app-name` with your actual Heroku app name:
```bash
heroku git:remote -a your-existing-app-name
```

## Step 4: Verify Environment Variables
Check that your tokens are set:
```bash
heroku config
```

If missing, set them:
```bash
heroku config:set DISCORD_TOKEN=your_discord_token
heroku config:set OPENAI_API_KEY=your_openai_key
```

## Step 5: Deploy Updated Bot
```bash
git init
git add .
git commit -m "Update to Ultra Bot v2.0 - 94 commands"
git push heroku main --force
```

## Step 6: Restart Bot Worker
```bash
heroku ps:scale worker=1
heroku restart
```

## Step 7: Monitor Deployment
```bash
heroku logs --tail
```

## What's Updated
- Enhanced utilities replacing music system
- All 94 commands optimized for stability
- Improved error handling
- Better performance monitoring

Your Ultra Bot will now be running the latest version with maximum Discord functionality on your existing Heroku app.