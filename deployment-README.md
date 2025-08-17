# Deployment Files

This directory contains all the files needed for deploying LexiGraph to production.

## Files Overview

### Backend (Render) Files
- `backend/requirements.txt` - Python dependencies
- `backend/Procfile` - Render process configuration
- `backend/render.yaml` - Render service configuration (optional)

### Frontend (Vercel) Files
- `frontend/vercel.json` - Vercel deployment configuration
- `frontend/.env.example` - Environment variable template

### Deployment Guide
- `DEPLOYMENT.md` - Complete deployment instructions
- `deploy.sh` - Helper script to verify deployment readiness

## Quick Start

1. Run the deployment helper:
   ```bash
   ./deploy.sh
   ```

2. Follow the instructions in `DEPLOYMENT.md`

3. Deploy backend to Render, then frontend to Vercel

4. Update environment variables with your actual URLs

## Environment Variables

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL` - Your Render backend URL

### Backend (Render)
- `PORT` - Automatically set by Render
- Add any API keys your app needs (Anthropic, OpenAI, etc.)

## Important Notes

- Make sure to update the CORS settings in your backend once you have your Vercel URL
- The output directory path has been fixed for deployment environments
- All API URLs in the frontend components now use environment variables
