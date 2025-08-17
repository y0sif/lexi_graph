#!/bin/bash

# LexiGraph Deployment Helper Script

echo "🚀 LexiGraph Deployment Helper"
echo "==============================="

# Check if we're in the project root
if [ ! -f "pyproject.toml" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "📝 Step 1: Preparing backend for deployment..."

# Navigate to backend directory
cd backend

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in backend directory"
    exit 1
fi

echo "✅ Backend requirements.txt found"

# Check if Procfile exists
if [ ! -f "Procfile" ]; then
    echo "❌ Procfile not found in backend directory"
    exit 1
fi

echo "✅ Backend Procfile found"

# Go back to project root
cd ..

echo "📝 Step 2: Preparing frontend for deployment..."

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

echo "✅ Frontend package.json found"

# Check if vercel.json exists
if [ ! -f "vercel.json" ]; then
    echo "❌ vercel.json not found in frontend directory"
    exit 1
fi

echo "✅ Frontend vercel.json found"

# Go back to project root
cd ..

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Deploy backend to Render:"
echo "   - Go to render.com"
echo "   - Create new Web Service"
echo "   - Connect your GitHub repo"
echo "   - Set root directory to 'backend'"
echo "   - Use build command: pip install -r requirements.txt"
echo "   - Use start command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "3. Deploy frontend to Vercel:"
echo "   - Go to vercel.com"
echo "   - Import your GitHub repo"
echo "   - Set root directory to 'frontend'"
echo "   - Add environment variable: NEXT_PUBLIC_API_URL=<your-render-url>"
echo ""
echo "4. Update CORS settings in backend with your Vercel URL"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT.md"
