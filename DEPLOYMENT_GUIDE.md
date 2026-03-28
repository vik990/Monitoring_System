# Deployment Guide for Electricity Monitor Dashboard

This guide will help you deploy your Django application with Tuya integration to Vercel and configure the necessary IP settings.

## Prerequisites

- Vercel account (https://vercel.com/)
- Tuya Developer account (https://developer.tuya.com/)
- Git repository with your project

## Step 1: Prepare Your Project

### 1.1 Environment Variables

Create a `.env` file in your project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Update the `.env` file with your actual credentials:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-vercel-url.vercel.app

# Tuya IoT Cloud Configuration
TUYA_ACCESS_ID=your-tuya-access-id
TUYA_ACCESS_SECRET=your-tuya-access-secret
TUYA_BASE_URL=https://openapi.tuyaeu.com
TUYA_DEVICE_ID=your-tuya-device-id

# Email Configuration (optional)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

### 1.2 Database Configuration

For production deployment, you'll need a database service. Options include:

- **Vercel Postgres** (recommended for Vercel)
- **PlanetScale** (MySQL-compatible)
- **Supabase** (PostgreSQL)
- **Railway** (PostgreSQL/MySQL)

## Step 2: Deploy to Vercel

### 2.1 Using Vercel CLI

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy your project:
```bash
vercel
```

4. Follow the prompts to configure your project.

### 2.2 Using Vercel Dashboard

1. Push your code to GitHub/GitLab/Bitbucket
2. Go to https://vercel.com/new
3. Import your Git repository
4. Configure the project settings:
   - Framework Preset: Other
   - Build Command: `python manage.py collectstatic --noinput`
   - Output Directory: `staticfiles`
   - Install Command: `pip install -r requirements.txt`

## Step 3: Configure Tuya IP Whitelist

### 3.1 Get Your Vercel Deployment URL

After deployment, Vercel will provide you with a URL like:
- `https://your-project-name.vercel.app`

### 3.2 Add URL to Tuya Whitelist

1. Log in to Tuya Developer Platform: https://developer.tuya.com/
2. Go to your project settings
3. Navigate to "API Authorization" or "IP Whitelist"
4. Add your Vercel deployment URL to the whitelist

**Note:** Vercel URLs are automatically whitelisted for Tuya API access, but you may need to add them manually in some cases.

### 3.3 Alternative: Use IP Detection

You can use the built-in IP detection tool:

1. Visit your deployed application
2. Navigate to `/ip-info/` endpoint
3. Copy the public IP address
4. Add this IP to your Tuya project's IP whitelist

## Step 4: Configure Environment Variables in Vercel

### 4.1 Using Vercel Dashboard

1. Go to your project settings in Vercel
2. Navigate to "Environment Variables"
3. Add all the environment variables from your `.env` file

### 4.2 Using Vercel CLI

```bash
vercel env add SECRET_KEY
vercel env add TUYA_ACCESS_ID
vercel env add TUYA_ACCESS_SECRET
vercel env add TUYA_BASE_URL
vercel env add TUYA_DEVICE_ID
# Add other variables as needed
```

Then deploy:
```bash
vercel --prod
```

## Step 5: Test Your Deployment

### 5.1 Test Tuya Connection

Visit these endpoints to test your setup:

1. **IP Information**: `https://your-project.vercel.app/ip-info/`
2. **Tuya Connection Test**: `https://your-project.vercel.app/test-tuya-connection/`

### 5.2 Test Dashboard

1. Visit your main dashboard: `https://your-project.vercel.app/`
2. Log in with your credentials
3. Check if Tuya live metrics are working

## Troubleshooting

### Common Issues

#### 1. Tuya API Connection Errors
- **Error**: "Tuya IP not allowed"
- **Solution**: Ensure your Vercel URL is added to Tuya IP whitelist

#### 2. Database Connection Errors
- **Error**: Database connection failed
- **Solution**: Configure proper database URL in environment variables

#### 3. Static Files Not Loading
- **Error**: CSS/JS files not found
- **Solution**: Ensure `collectstatic` runs during build

#### 4. Environment Variables Not Loading
- **Error**: Missing configuration
- **Solution**: Verify environment variables are set in Vercel dashboard

### Debug Commands

Test your application locally with production settings:

```bash
# Set environment variables
export DEBUG=False
export SECRET_KEY=your-secret-key
export TUYA_ACCESS_ID=your-access-id
# ... other variables

# Run development server
python manage.py runserver
```

## Local Development with ngrok

For testing Tuya integration locally:

### 1. Install ngrok
```bash
# Download from https://ngrok.com/download
# Or use package manager
brew install ngrok  # macOS
choco install ngrok  # Windows
```

### 2. Start Local Server
```bash
python manage.py runserver
```

### 3. Expose Local Server
```bash
ngrok http 8000
```

### 4. Add ngrok URL to Tuya
Copy the generated HTTPS URL and add it to your Tuya IP whitelist.

## Production Best Practices

### 1. Security
- Set `DEBUG=False` in production
- Use strong secret keys
- Enable HTTPS (automatic with Vercel)
- Regularly update dependencies

### 2. Performance
- Use a CDN for static files
- Enable caching where appropriate
- Monitor application performance

### 3. Monitoring
- Set up error tracking (e.g., Sentry)
- Monitor Tuya API usage
- Track application metrics

### 4. Backups
- Regular database backups
- Git-based code backups
- Environment variable documentation

## Support

If you encounter issues:

1. Check the deployment logs in Vercel dashboard
2. Test Tuya connection using the provided endpoints
3. Verify all environment variables are correctly set
4. Check Tuya Developer Console for API errors

For additional help, refer to:
- [Vercel Django Documentation](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Tuya Developer Documentation](https://developer.tuya.com/en/docs/iot)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)