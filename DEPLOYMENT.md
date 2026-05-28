# Deployment Guide

## Overview

This guide covers deploying Breathe ESG to production using Railway, Render, or Heroku.

## Prerequisites

1. **Git repository** - Push code to GitHub
2. **Environment variables** - Prepare .env values
3. **Database** - PostgreSQL 15+
4. **Domain** (optional) - Custom domain for UI

## Deployment Platforms

### 1. Railway (Recommended)

#### Setup

1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your Breathe repository
4. Authorize Railway to access GitHub

#### Configure Services

1. **Create PostgreSQL plugin**
   - Click **Add Service** → **PostgreSQL**
   - Use default settings
   - Note the database URL

2. **Backend Service**
   - Settings → Environment
   - Add variables from `.env.example`
   - Set `DATABASE_URL` to PostgreSQL connection string
   - Set `ALLOWED_HOSTS=*.railway.app`
   - Root directory: `backend`

3. **Frontend Service**
   - Settings → Environment
   - Set `VITE_API_URL=https://<backend-url>/api`
   - Root directory: `frontend`
   - Build command: `npm install && npm run build`
   - Start command: `npm run preview`

4. **Run migrations**
   ```bash
   railway run python manage.py migrate
   railway run python manage.py shell < manage_commands/seed_data.py
   ```

#### Deploy

- Push to main branch - Railway auto-deploys
- Monitor logs: Railway dashboard

### 2. Render

#### Setup

1. Go to [render.com](https://render.com)
2. Click **New +** → **Blueprint**
3. Use provided `render.yaml`
4. Connect GitHub repository

#### Configure

1. Set environment variables:
   - `DJANGO_SECRET_KEY` - Generate random string
   - `EMAIL_HOST_PASSWORD` - If using email
   
2. Configure PostgreSQL:
   - Add trusted IP: `0.0.0.0/0` (or restrict)
   - Note connection string

3. Run migrations:
   ```bash
   render exec -s breathe-backend python manage.py migrate
   ```

#### Deploy

- Render auto-deploys on git push
- View at `https://breathe-backend.onrender.com`

### 3. Heroku

#### Setup

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login

# Create apps
heroku create breathe-api
heroku create breathe-app
```

#### Configure

1. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:standard-0 -a breathe-api
   ```

2. **Set environment variables**
   ```bash
   heroku config:set DJANGO_SECRET_KEY=... -a breathe-api
   heroku config:set DEBUG=False -a breathe-api
   ```

3. **Deploy backend**
   ```bash
   cd backend
   git subtree push --prefix backend heroku main
   ```

4. **Run migrations**
   ```bash
   heroku run python manage.py migrate -a breathe-api
   ```

5. **Deploy frontend**
   ```bash
   cd frontend
   heroku config:set VITE_API_URL=https://breathe-api.herokuapp.com/api -a breathe-app
   git subtree push --prefix frontend heroku main
   ```

## Post-Deployment

### 1. Create Admin User

```bash
# Railway
railway run python manage.py createsuperuser

# Render
render exec -s breathe-backend python manage.py createsuperuser

# Heroku
heroku run python manage.py createsuperuser -a breathe-api
```

### 2. Seed Data

```bash
# Railway
railway run python manage.py shell < manage_commands/seed_data.py

# Render
render exec -s breathe-backend python manage.py shell < manage_commands/seed_data.py

# Heroku
heroku run python manage.py shell -a breathe-api < manage_commands/seed_data.py
```

### 3. Test Application

1. Visit frontend URL
2. Login with demo credentials
3. Upload test CSV from `sample_data/`
4. Verify records process correctly

## Monitoring

### Logs

- **Railway**: Dashboard → Logs tab
- **Render**: Service → Logs
- **Heroku**: `heroku logs --tail -a breathe-api`

### Performance

- Monitor database connections
- Check API response times
- Watch for memory usage

## Scaling

### Railway

- Go to Service → Instance
- Increase plan (pro, teams, pay-as-you-go)

### Render

- Service settings → Plan
- Upgrade from Starter to Standard

### Heroku

- Increase dyno size
- Add worker dynos for background jobs

## Custom Domain

### Railway

1. Service → Settings → Custom Domain
2. Add your domain
3. Update DNS records with provided CNAME

### Render

1. Service → Custom Domain
2. Add domain
3. Update DNS settings

### Heroku

1. `heroku domains:add www.yourdomain.com -a breathe-api`
2. Update DNS with provided CNAME

## Troubleshooting

### Database Connection Errors

```bash
# Check DATABASE_URL is set
heroku config -a breathe-api | grep DATABASE_URL

# Verify migrations ran
heroku run python manage.py showmigrations -a breathe-api
```

### 404 on Frontend

- Check `VITE_API_URL` points to correct backend
- Verify CORS settings in Django
- Check frontend is built with `npm run build`

### Static Files Not Loading

```bash
# Collect static files
heroku run python manage.py collectstatic --no-input -a breathe-api
```

### 500 Errors

1. Check backend logs
2. Verify all migrations ran
3. Check environment variables
4. Verify PostgreSQL is accessible

## Continuous Deployment

GitHub Actions workflow runs on push:
- Runs Python tests
- Runs linting
- Builds Docker images
- Can auto-deploy on success

See `.github/workflows/ci.yml`

## Backup & Recovery

### Database Backup

- **Railway**: Automatic daily backups
- **Render**: Configure backup schedule
- **Heroku**: Use PG Backups add-on

### Manual Backup

```bash
# Export data
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] `DJANGO_SECRET_KEY` is unique & secret
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS enabled on domain
- [ ] CORS origins restricted
- [ ] Database password is strong
- [ ] SSH keys configured
- [ ] Regular security updates

---

**Need help?** Check application logs and Django error messages for detailed diagnostics.
