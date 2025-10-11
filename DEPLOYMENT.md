# 🚀 DEPLOYMENT GUIDE
# ArtacomFTTHBilling_V2

## 📋 **Table of Contents**
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Deployment Options](#deployment-options)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Manual Deployment](#manual-deployment)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 **PREREQUISITES**

### **Server Requirements:**
- **OS:** Ubuntu 20.04+ or CentOS 8+
- **RAM:** Minimum 4GB
- **Storage:** 20GB+
- **Node.js:** v18+
- **Python:** 3.10+
- **PostgreSQL:** 13+
- **Redis:** 6+

### **Development Tools:**
- **Git:** v2.30+
- **Android Studio:** Latest
- **VS Code:** Latest

---

## 🔧 **ENVIRONMENT SETUP**

### **Backend Configuration:**
```bash
# Clone repository
git clone https://github.com/your-username/ArtacomFTTHBilling_V2.git
cd ArtacomFTTHBilling_V2

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment files
cp .env.example .env
# Edit .env dengan konfigurasi yang sesuai
```

### **Environment Variables (.env):**
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/artacom_billing
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# Production Settings
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## 🚀 **DEPLOYMENT OPTIONS**

### **Option 1: Docker Container (Recommended)**
```bash
# Build Docker image
docker build -t artacom-billing:latest .

# Run with Docker Compose
docker-compose up -d
```

### **Option 2: Traditional Server Deployment**
```bash
# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend (nginx terintegrasi)
# Serve dari dist/ dengan nginx
```

### **Option 3: Cloud Platform**
- **AWS EC2** dengan Docker
- **Google Cloud Platform**
- **DigitalOcean** Droplets
- **Vercel** (frontend)

---

## 🔄 **CI/CD PIPELINE**

### **Automated Build & Deploy:**
1. **Push ke main branch** → Otomatis build
2. **Pull Request** → Run tests → Build APK
3. **Deployment** → Upload APK ke artifacts
4. **Optional deployment** → Deploy ke server

### **CI/CD Features:**
- ✅ **Type checking** (Vue.js + TypeScript)
- ✅ **Unit testing** (frontend & backend)
- ✅ **Security scanning**
- ✅ **APK build** (Debug & Release)
- ✅ **Artifact management**
- ✅ **Multi-environment support**

---

## 📦 **MANUAL DEPLOYMENT**

### **Backend Deployment:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database
createdb artacom_billing
psql -U postgres -d artacom_billing < database/schema.sql

# 3. Run migrations
alembic upgrade head

# 4. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **Frontend Deployment:**
```bash
# 1. Build production version
cd frontend
npm run build

# 2. Configure web server (nginx)
sudo cp -r dist/* /var/www/html/

# 3. Start nginx
sudo systemctl start nginx
```

### **Android APK Deployment:**
```bash
# 1. Install ADB
# Download dan install Android SDK

# 2. Enable USB debugging
# Enable Developer Options pada Android device

# 3. Install APK
adb install frontend/android/app/build/outputs/apk/release/app-release.apk

# 4. Testing
# Buka aplikasi dan uji semua fitur
```

---

## 🔍 **TROUBLESHOOTING**

### **Build Errors:**
```bash
# Clean build cache
npm run clean && npm run build

# Reinstall dependencies
rm -rf node_modules && npm install
```

### **APK Installation Errors:**
```bash
# Enable USB debugging pada device
# Buka Developer Options → USB Debugging

# Check Android version compatibility
adb devices
adb shell getprop ro.build.version.sdk
```

### **Database Connection Errors:**
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d artacom_billing
```

### **API Connection Issues:**
```bash
# Test backend API
curl -X GET http://localhost:8000/api/status

# Test frontend routing
curl -I http://localhost:5173
```

---

## 📱 **MONITORING & LOGS**

### **Application Logs:**
```bash
# Backend logs
tail -f logs/app.log

# Access logs via mobile
curl http://your-domain.com/logs
```

### **Database Monitoring:**
```sql
-- Check active connections
SELECT * FROM pg_stat_activity;

-- Monitor slow queries
SELECT * FROM pg_stat_statements WHERE mean_exec_time > 1000;
```

### **API Monitoring:**
- Application Performance Monitoring (APM)
- Error tracking and alerting
- Uptime monitoring

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **Backend:**
- Database connection pooling
- Query optimization
- Caching strategy
- Load balancing

### **Frontend:**
- Bundle size optimization
- Lazy loading
- Service Worker for caching
- CDN integration

### **Mobile:**
- APK size optimization
- Resource compression
- Network request optimization
- Local storage caching

---

## 🔄 **UPDATE STRATEGY**

### **Rollback Plan:**
1. Backup current version
2. Keep previous build
3. Revert jika diperlukan

### **Blue-Green Deployment:**
1. Deploy ke staging environment
2. Run smoke tests
3. Gradual production rollout

### **Zero-Downtime:**
- Load balancer configuration
- Health checks
- Graceful shutdown
- Auto-scaling

---

## 🔐 **SECURITY CONSIDERATIONS**

### **Production Security:**
- HTTPS enforcement
- API rate limiting
- Input validation
- SQL injection prevention
- CORS configuration
- Security headers

### **Mobile Security:**
- APK signing
- Certificate pinning
- Root detection
- Data encryption
- Secure storage

### **Data Protection:**
- Database encryption
- Backup strategy
- Access control
- Audit logging
- Data retention policy

---

## 📞 **BACKUP STRATEGY**

### **Database Backups:**
```bash
# Automated daily backups
pg_dump artacom_billing > backup_$(date +%Y%m%d).sql

# Incremental backups
pg_basebackup artacom_billing /backups/incremental/
```

### **Application Backups:**
```bash
# Code repositories
git archive --format zip -9 ../backup/frontend-$(date +%Y%m%d).zip

# Configuration files
tar -czf ../backup/config-$(date +%Y%m%d).tar.gz .env
```

### **APK Backups:**
```bash
# Versioned APK storage
mkdir -p releases/
cp *.apk releases/v$(date +%Y%m%d)/
```

---

## 📞 **NEXT STEPS**

1. **Testing Phase:**
   - Install APK di test device
   - Uji semua fitur utama
   - Validasi API integration

2. **Staging Deployment:**
   - Deploy ke staging environment
   - Load testing
   - Performance monitoring

3. **Production Release:**
   - Generate signed APK
   - Deploy ke production server
   - Monitor performance

4. **Post-Deployment:**
   - Monitor logs
   - Collect user feedback
   - Plan improvements

---

**🚀 Your ArtacomFTTHBilling_V2 is now fully automated and production-ready with CI/CD pipeline!** 🎯

---

*Last Updated: October 11, 2025*
*Version: 1.0*