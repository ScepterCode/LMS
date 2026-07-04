# 🚀 Deployment Guide - Nigerian LMS

Complete guide for deploying Phase 1 MVP to production.

---

## 📋 Pre-Deployment Checklist

### Backend Preparation
- [ ] Update `JWT_SECRET` to a secure random string (min 32 characters)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure production database URL
- [ ] Update `ALLOWED_ORIGINS` to production frontend URL
- [ ] Review all environment variables
- [ ] Test database connection
- [ ] Run security audit

### Frontend Preparation
- [ ] Update `NEXT_PUBLIC_API_URL` to production backend
- [ ] Test production build locally (`npm run build && npm start`)
- [ ] Verify all API calls work
- [ ] Check responsive design
- [ ] Test authentication flow
- [ ] Review error handling

### Database Preparation
- [ ] Backup development database
- [ ] Create production database
- [ ] Run schema migration (`phase1_minimal_schema.sql`)
- [ ] Create system admin account
- [ ] Verify RLS policies (if using Supabase)
- [ ] Test database connection from backend

---

## 🌐 Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend) ⭐ Recommended

#### Why This Combo?
- **Vercel**: Best for Next.js (made by Next.js creators)
- **Railway**: Simple, affordable backend hosting
- **Total Cost**: ~$5-15/month to start

---

### 🎨 Frontend Deployment (Vercel)

#### Step 1: Prepare Repository
```bash
# Initialize git if not done
cd frontend
git init
git add .
git commit -m "Initial frontend commit"

# Push to GitHub
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

#### Step 2: Deploy to Vercel

1. **Go to Vercel**: https://vercel.com
2. **Click "Add New Project"**
3. **Import from GitHub**: Select your repository
4. **Configure Project**:
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

5. **Environment Variables**:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   NEXT_PUBLIC_APP_NAME=Nigerian LMS
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```

6. **Click "Deploy"**

7. **Custom Domain** (Optional):
   - Settings → Domains
   - Add your domain (e.g., `app.nigerianlms.com`)
   - Follow DNS configuration instructions

#### Step 3: Verify Deployment

Visit your Vercel URL:
- Landing page loads ✅
- Login page works ✅
- Check browser console for errors ❌
- Test registration ✅

---

### ⚙️ Backend Deployment (Railway)

#### Step 1: Prepare Repository
```bash
cd backend
git init
git add .
git commit -m "Initial backend commit"
git push -u origin main
```

#### Step 2: Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **Click "New Project"**
3. **Deploy from GitHub**: Select your repository
4. **Add PostgreSQL**:
   - Click "New" → "Database" → "PostgreSQL"
   - Note the connection string

#### Step 3: Configure Backend Service

1. **Settings → Environment Variables**:
   ```env
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   JWT_SECRET=your-super-secure-random-32-char-string
   SECRET_KEY=your-super-secure-random-32-char-string
   ENVIRONMENT=production
   DEBUG=false
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
   ```

2. **Settings → Deploy**:
   ```
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Settings → Networking**:
   - Generate Domain (e.g., `nigerian-lms-production.up.railway.app`)
   - Or add custom domain

#### Step 4: Run Database Migration

1. **Connect to Railway Postgres**:
   ```bash
   # Get connection string from Railway
   psql "postgresql://postgres:password@host:port/railway"
   ```

2. **Run schema**:
   ```bash
   # Copy contents of database/phase1_minimal_schema.sql
   # Paste into psql console
   ```

#### Step 5: Verify Deployment

Test endpoints:
```bash
curl https://your-backend-url.railway.app/health
curl https://your-backend-url.railway.app/docs
```

---

### 🔄 Update Frontend with Backend URL

1. **Go to Vercel Dashboard**
2. **Settings → Environment Variables**
3. **Update `NEXT_PUBLIC_API_URL`**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```
4. **Redeploy** (automatic)

---

## 🎯 Option 2: Alternative Platforms

### Backend Alternatives

#### Render.com
```yaml
# render.yaml
services:
  - type: web
    name: nigerian-lms-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: nigerian-lms-db
          property: connectionString
```

#### Fly.io
```toml
# fly.toml
app = "nigerian-lms-backend"

[build]
  builder = "paketobuildpacks/builder:base"
  buildpacks = ["gcr.io/paketo-buildpacks/python"]

[[services]]
  internal_port = 8000
  protocol = "tcp"
```

#### DigitalOcean App Platform
- One-click Python app deployment
- $5-12/month
- Easy scaling

### Frontend Alternatives

#### Netlify
- Similar to Vercel
- Great Next.js support
- Free tier available

#### Cloudflare Pages
- Edge deployment
- Fast global CDN
- Free tier

---

## 💾 Database Options

### Option 1: Supabase (Recommended)
- **Pros**: Managed PostgreSQL, realtime, storage, auth
- **Pricing**: Free tier (500MB), then $25/month
- **Setup**: Already configured in your project

### Option 2: Railway PostgreSQL
- **Pros**: Integrated with backend hosting
- **Pricing**: ~$5/month (500MB)
- **Setup**: One-click from Railway dashboard

### Option 3: Neon
- **Pros**: Serverless PostgreSQL, branching
- **Pricing**: Free tier (3GB), then $19/month
- **URL**: https://neon.tech

---

## 🔐 Security Configuration

### Generate Secure Secrets

```bash
# JWT Secret (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use online generator
# https://www.random.org/strings/
```

### SSL/HTTPS

**Vercel**: Automatic HTTPS ✅  
**Railway**: Automatic HTTPS ✅  
**Custom Domain**: Configure SSL certificate

### CORS Configuration

Update backend `.env`:
```env
# Production frontend URL
ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com

# Multiple origins (comma-separated)
ALLOWED_ORIGINS=https://app1.com,https://app2.com
```

### Environment Security

**Never commit**:
- `.env` files
- Database passwords
- API keys
- JWT secrets

**Use**:
- Platform environment variables
- Secret management services
- `.env.example` for templates

---

## 🧪 Post-Deployment Testing

### 1. Health Checks
```bash
# Backend health
curl https://your-backend.railway.app/health

# Expected response
{
  "status": "healthy",
  "database": {...}
}
```

### 2. Frontend Loading
- Visit `https://your-app.vercel.app`
- Check landing page loads
- Verify no console errors
- Test mobile responsive

### 3. Authentication Flow
- Register new school
- Login as new school admin
- Verify dashboard loads
- Test logout
- Login as system admin

### 4. API Integration
- Open Network tab in browser
- Perform actions (login, register)
- Verify API calls succeed (200 status)
- Check request/response headers

### 5. Database Connection
- Create test account
- Verify data persists
- Check in database directly
- Test with multiple users

### 6. Performance
- Run Lighthouse audit
- Target scores:
  - Performance: 90+
  - Accessibility: 90+
  - Best Practices: 90+
  - SEO: 90+

---

## 📊 Monitoring & Analytics

### Backend Monitoring

#### Railway (Built-in)
- Deployment logs
- Application metrics
- CPU/Memory usage

#### Sentry (Recommended)
```bash
pip install sentry-sdk
```

```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
)
```

### Frontend Monitoring

#### Vercel Analytics (Built-in)
- Automatically enabled
- Web Vitals tracking
- Performance insights

#### Google Analytics
```typescript
// app/layout.tsx
import Script from 'next/script'

<Script
  src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"
  strategy="afterInteractive"
/>
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions (Optional)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Backend
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Frontend
        run: |
          cd frontend
          npm install
          npm run build
```

---

## 💰 Cost Estimation

### Minimal Setup (MVP/Testing)
```
Backend (Railway):     $5/month
Database (Railway):    $5/month
Frontend (Vercel):     $0/month (free tier)
Domain:                $12/year
-----------------------------------
Total:                 ~$10-15/month
```

### Production Setup (Launch)
```
Backend (Railway):     $20/month (Pro)
Database (Supabase):   $25/month (Pro)
Frontend (Vercel):     $20/month (Pro)
Domain:                $12/year
Monitoring (Sentry):   $26/month (Team)
-----------------------------------
Total:                 ~$90-100/month
```

### Scale (100+ Schools)
```
Backend (Railway):     $50/month (scaled)
Database (Supabase):   $99/month (Team)
Frontend (Vercel):     $20/month
CDN/Storage:           $20/month
Monitoring:            $26/month
Email Service:         $10/month
-----------------------------------
Total:                 ~$225/month
```

---

## 🚨 Troubleshooting

### Backend Issues

**Problem**: 500 errors on deployment
```bash
# Check Railway logs
railway logs --tail 100

# Common fixes:
- Verify DATABASE_URL is set
- Check JWT_SECRET exists
- Ensure all dependencies installed
```

**Problem**: Database connection fails
```bash
# Test connection
psql $DATABASE_URL

# Verify:
- Connection string format correct
- Database exists
- User has permissions
```

### Frontend Issues

**Problem**: API calls fail (CORS errors)
```
Solution:
1. Check ALLOWED_ORIGINS in backend
2. Verify NEXT_PUBLIC_API_URL points to backend
3. Ensure HTTPS on both ends
```

**Problem**: Environment variables not working
```
Solution:
1. Redeploy after adding env vars
2. Check var names start with NEXT_PUBLIC_
3. Clear .next cache and rebuild
```

---

## ✅ Launch Checklist

### Pre-Launch
- [ ] All tests passing
- [ ] Environment variables set
- [ ] Database migrated
- [ ] System admin account created
- [ ] HTTPS enabled
- [ ] Custom domain configured
- [ ] Error monitoring active
- [ ] Backup strategy in place

### Launch Day
- [ ] Monitor error logs
- [ ] Test all critical flows
- [ ] Verify email delivery (Phase 2)
- [ ] Check performance metrics
- [ ] Have rollback plan ready

### Post-Launch
- [ ] Monitor user signups
- [ ] Track error rates
- [ ] Review performance
- [ ] Gather user feedback
- [ ] Plan Phase 2 features

---

## 📞 Support Resources

### Documentation
- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **Vercel**: https://vercel.com/docs
- **Railway**: https://docs.railway.app
- **Supabase**: https://supabase.com/docs

### Community
- **Next.js Discord**: https://nextjs.org/discord
- **FastAPI Discord**: https://discord.gg/fastapi
- **Vercel Discord**: https://vercel.com/discord

---

## 🎉 You're Ready to Deploy!

Follow the steps above to get your Nigerian LMS live on the internet. Start with the recommended stack (Vercel + Railway) for the easiest deployment experience.

**Estimated time to deploy**: 30-60 minutes

---

**Guide Version**: 1.0.0  
**Last Updated**: June 4, 2026  
**For**: Phase 1 MVP
