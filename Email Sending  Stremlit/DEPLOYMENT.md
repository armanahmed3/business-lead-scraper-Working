# 🚀 LeadAI Pro - Deployment Guide

Complete guide for deploying LeadAI Pro to production environments.

## 📋 Prerequisites

- Python 3.8+
- pip package manager
- Git
- Database (PostgreSQL recommended for production)
- SMTP email service
- Domain name (optional)

## 🔧 Local Development Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Lead-Stremlit
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp env_example.txt .env
# Edit .env with your configuration
```

### 3. Run Locally
```bash
python run.py
```

Access:
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🌐 Production Deployment

### Option 1: Render (Recommended)

#### Backend Deployment
1. **Create Render Account**: Sign up at render.com
2. **Connect Repository**: Link your GitHub repository
3. **Create Web Service**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.8+

#### Frontend Deployment
1. **Create Static Site**:
   - Build Command: `pip install streamlit && streamlit run app.py --server.port 8501`
   - Publish Directory: `.`

#### Environment Variables
Set these in Render dashboard:
```env
DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your-production-secret-key
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=LeadAI Pro
WS_METRICS_URL=ws://your-backend-domain/ws/metrics
```

### Option 2: Railway

#### Backend Deployment
1. **Install Railway CLI**: `npm install -g @railway/cli`
2. **Login**: `railway login`
3. **Initialize Project**: `railway init`
4. **Deploy**: `railway up`

#### Frontend Deployment
1. **Create New Service**: `railway add`
2. **Configure**: Set build and start commands
3. **Deploy**: `railway up`

### Option 3: Heroku

#### Backend Deployment
1. **Install Heroku CLI**
2. **Create App**: `heroku create your-app-name`
3. **Set Environment Variables**:
   ```bash
   heroku config:set DATABASE_URL=postgresql://...
   heroku config:set SECRET_KEY=your-secret-key
   ```
4. **Deploy**: `git push heroku main`

#### Frontend Deployment
1. **Create Procfile**: `echo "web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0" > Procfile`
2. **Deploy**: `git push heroku main`

### Option 4: VPS/Cloud Server

#### Using Docker (Optional)
```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8501

CMD ["python", "run.py"]
```

#### Manual Setup
1. **Server Setup**:
   ```bash
   sudo apt update
   sudo apt install python3-pip postgresql nginx
   ```

2. **Application Setup**:
   ```bash
   git clone <repository-url>
   cd Lead-Stremlit
   pip3 install -r requirements.txt
   ```

3. **Database Setup**:
   ```bash
   sudo -u postgres createdb leadai
   sudo -u postgres createuser leadai_user
   sudo -u postgres psql -c "ALTER USER leadai_user PASSWORD 'your_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE leadai TO leadai_user;"
   ```

4. **Nginx Configuration**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Systemd Service**:
   ```ini
   [Unit]
   Description=LeadAI Pro
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/Lead-Stremlit
   ExecStart=/usr/bin/python3 run.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

## 🗄️ Database Setup

### PostgreSQL (Production)
```sql
CREATE DATABASE leadai;
CREATE USER leadai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE leadai TO leadai_user;
```

### SQLite (Development)
No setup required - automatically created.

## 📧 Email Configuration

### Gmail Setup
1. Enable 2-factor authentication
2. Generate app password
3. Use app password in SMTP_PASSWORD

### Gmail OAuth2 (Optional)
Provide OAuth2 values in the SMTP profile UI (no .env variables required): Client ID, Client Secret, Refresh Token. The app will fetch access tokens at send time and authenticate using XOAUTH2.

### SendGrid Setup
1. Create SendGrid account
2. Generate API key
3. Update SMTP settings:
   ```env
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   ```

### Mailgun Setup
1. Create Mailgun account
2. Get SMTP credentials
3. Update SMTP settings:
   ```env
   SMTP_SERVER=smtp.mailgun.org
   SMTP_PORT=587
   SMTP_USERNAME=your-mailgun-username
   SMTP_PASSWORD=your-mailgun-password
   ```

## 🔒 Security Configuration

### SSL/HTTPS Setup
1. **Let's Encrypt** (Free):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Cloudflare** (Free):
   - Add domain to Cloudflare
   - Enable SSL/TLS encryption
   - Set SSL mode to "Full (strict)"

### Environment Security
```env
# Use strong, unique secret key
SECRET_KEY=your-very-long-random-secret-key-here

# Use production database
DATABASE_URL=postgresql://user:pass@host:port/db

# Enable debug mode only in development
DEBUG=False

# Set allowed hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📊 Monitoring & Analytics

### Application Monitoring
1. **Uptime Monitoring**: UptimeRobot, Pingdom
2. **Error Tracking**: Sentry, Rollbar
3. **Performance**: New Relic, DataDog

### Database Monitoring
1. **PostgreSQL Monitoring**: pgAdmin, Grafana
2. **Query Performance**: pg_stat_statements
3. **Backup Monitoring**: Automated backups

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
name: Deploy LeadAI Pro

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: python -m pytest tests/
    
    - name: Deploy to production
      run: |
        # Your deployment commands here
        echo "Deploying to production..."
```

## 📈 Performance Optimization

### Backend Optimization
1. **Database Indexing**: Add indexes for frequently queried fields
2. **Caching**: Implement Redis for session and data caching
3. **Connection Pooling**: Configure database connection pooling
4. **Async Processing**: Use Celery for background tasks

### Frontend Optimization
1. **Static Assets**: Use CDN for static files
2. **Caching**: Implement browser caching
3. **Compression**: Enable gzip compression
4. **Minification**: Minify CSS and JavaScript

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U leadai_user -d leadai
```

#### Email Sending Issues
```bash
# Test SMTP connection
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email@gmail.com', 'your-app-password')
print('SMTP connection successful')
smtp.quit()
"
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8501

# Kill processes using ports
sudo kill -9 <PID>
```

### Logs and Debugging
```bash
# Application logs
tail -f /var/log/leadai/app.log

# System logs
sudo journalctl -u leadai -f

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 📞 Support

For deployment support:
- Email: support@leadai.com
- Documentation: https://docs.leadai.com
- Issues: GitHub Issues

## 🎉 Success!

Once deployed, your LeadAI Pro platform will be available at:
- Frontend: https://yourdomain.com
- Backend API: https://yourdomain.com/api
- API Documentation: https://yourdomain.com/api/docs

Congratulations on deploying your AI-powered lead management platform! 🚀
