# LexiGraph Deployment Guide

This guide will help you deploy LexiGraph with the frontend on Vercel and the backend on Render.

## Prerequisites

- GitHub account
- Vercel account (free tier available)
- Render account (free tier available)
- Your code pushed to a GitHub repository

## Backend Deployment (Render)

### Step 1: Push your code to GitHub
Ensure your backend code is in a GitHub repository.

### Step 2: Create a new Render service
1. Go to [Render](https://render.com) and sign in
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend` (if your backend is in a subdirectory)

### Step 3: Set environment variables
In your Render service settings, add any required environment variables:
- `PYTHON_VERSION`: `3.13.0`
- Any API keys your application needs

### Step 4: Deploy
Click "Deploy" and wait for the deployment to complete. Note your service URL (e.g., `https://your-service-name.onrender.com`).

## Frontend Deployment (Vercel)

### Step 1: Update API URL
Update the API URLs in your frontend components to point to your Render backend:

```bash
# In frontend directory
cp .env.example .env.local
```

Edit `.env.local` and set:
```
NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com
```

### Step 2: Deploy to Vercel
1. Go to [Vercel](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend` (if your frontend is in a subdirectory)
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 3: Set environment variables
In your Vercel project settings → Environment Variables, add:
- `NEXT_PUBLIC_API_URL`: Your Render backend URL

### Step 4: Deploy
Click "Deploy" and wait for the deployment to complete.

## Post-Deployment

### Update CORS settings
Make sure your backend's CORS settings include your Vercel domain. The current configuration allows all origins, but you can restrict it to your specific domains for better security:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-app.vercel.app",  # Your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Test the deployment
1. Visit your Vercel frontend URL
2. Try creating a knowledge graph
3. Verify that the backend is responding correctly

## Troubleshooting

### Common Issues

1. **CORS errors**: Check that your backend allows requests from your Vercel domain
2. **API connection issues**: Verify the `NEXT_PUBLIC_API_URL` environment variable
3. **Build failures**: Check the build logs in Vercel/Render for specific error messages
4. **Missing dependencies**: Ensure all dependencies are listed in `requirements.txt` and `package.json`

### Environment Variables

Make sure these are set correctly:

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL`: Your Render backend URL

**Backend (Render):**
- `PORT`: Automatically set by Render
- Any API keys your app requires (Anthropic, OpenAI, etc.)

## Production Considerations

1. **Security**: 
   - Use specific CORS origins instead of wildcard
   - Store API keys securely as environment variables
   - Enable HTTPS

2. **Performance**:
   - Consider using a CDN for static assets
   - Implement caching strategies
   - Monitor response times

3. **Monitoring**:
   - Set up error tracking (Sentry, etc.)
   - Monitor uptime and performance
   - Set up alerts for failures

## Domain Configuration (Optional)

### Custom Domain for Vercel
1. In Vercel project settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed

### Custom Domain for Render
1. In Render service settings → Custom Domains
2. Add your custom domain
3. Configure DNS records as instructed

Remember to update your CORS and environment variables when using custom domains.
