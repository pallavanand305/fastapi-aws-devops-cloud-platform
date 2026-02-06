# Deployment Guide

## Overview

This guide covers deploying the ML Workflow Orchestration Platform to various environments.

## Prerequisites

- Docker and Docker Compose
- Access to container registry (Docker Hub, AWS ECR, etc.)
- Database server (PostgreSQL 13+)
- Redis server (6.0+)
- SSL/TLS certificates (for production)

## Environment Configuration

### Environment Variables

Create a `.env` file for each environment:

```env
# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Database
DB_HOST=your-db-host.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ml_platform
DB_USER=ml_platform_user
DB_PASSWORD=<secure-password>
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_HOST=your-redis-host.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>
REDIS_DB=0

# JWT
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://your-frontend.com"]
CORS_ALLOW_CREDENTIALS=true

# AWS (if using AWS services)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_S3_BUCKET=ml-platform-data

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
LOG_LEVEL=INFO

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-password>
SMTP_FROM=noreply@your-domain.com
```

### Generating Secure Keys

```bash
# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate database password
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Docker Deployment

### Building the Image

```bash
# Build production image
docker build -t ml-platform:latest -f Dockerfile .

# Tag for registry
docker tag ml-platform:latest your-registry/ml-platform:latest
docker tag ml-platform:latest your-registry/ml-platform:v1.0.0

# Push to registry
docker push your-registry/ml-platform:latest
docker push your-registry/ml-platform:v1.0.0
```

### Running with Docker Compose

1. **Create production docker-compose file** (`docker-compose.prod.yml`):

```yaml
version: '3.8'

services:
  app:
    image: your-registry/ml-platform:latest
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

2. **Start services**:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Run database migrations**:

```bash
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

4. **Create admin user**:

```bash
docker-compose -f docker-compose.prod.yml exec app python scripts/setup.py
```

### Nginx Configuration

Create `nginx.conf` for reverse proxy:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 100M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm 3+ installed

### Kubernetes Manifests

1. **Create namespace**:

```bash
kubectl create namespace ml-platform
```

2. **Create secrets**:

```bash
kubectl create secret generic ml-platform-secrets \
  --from-literal=db-password=<password> \
  --from-literal=redis-password=<password> \
  --from-literal=jwt-secret=<secret> \
  -n ml-platform
```

3. **Deploy application** (`k8s/deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-platform
  namespace: ml-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-platform
  template:
    metadata:
      labels:
        app: ml-platform
    spec:
      containers:
      - name: app
        image: your-registry/ml-platform:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ml-platform-secrets
              key: db-password
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ml-platform-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ml-platform
  namespace: ml-platform
spec:
  selector:
    app: ml-platform
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

4. **Apply manifests**:

```bash
kubectl apply -f k8s/deployment.yaml
```

### Helm Chart (Recommended)

Create a Helm chart for easier management:

```bash
helm create ml-platform-chart
```

Install the chart:

```bash
helm install ml-platform ./ml-platform-chart \
  --namespace ml-platform \
  --create-namespace \
  --set image.tag=v1.0.0 \
  --set database.password=<password>
```

## AWS Deployment

### Using AWS ECS

1. **Create ECR repository**:

```bash
aws ecr create-repository --repository-name ml-platform
```

2. **Push image to ECR**:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag ml-platform:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ml-platform:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ml-platform:latest
```

3. **Create ECS task definition and service** (use AWS Console or Terraform)

### Using AWS Elastic Beanstalk

1. **Install EB CLI**:

```bash
pip install awsebcli
```

2. **Initialize and deploy**:

```bash
eb init -p docker ml-platform
eb create ml-platform-prod
eb deploy
```

## Database Setup

### PostgreSQL

1. **Create database**:

```sql
CREATE DATABASE ml_platform;
CREATE USER ml_platform_user WITH PASSWORD '<secure-password>';
GRANT ALL PRIVILEGES ON DATABASE ml_platform TO ml_platform_user;
```

2. **Run migrations**:

```bash
alembic upgrade head
```

3. **Backup strategy**:

```bash
# Daily backup
pg_dump -h <host> -U ml_platform_user ml_platform > backup_$(date +%Y%m%d).sql

# Restore
psql -h <host> -U ml_platform_user ml_platform < backup_20260206.sql
```

### Redis

For production, use managed Redis (AWS ElastiCache, Redis Cloud, etc.) with:
- Persistence enabled
- Automatic failover
- Regular backups

## Monitoring Setup

### Prometheus

1. **Add Prometheus scrape config**:

```yaml
scrape_configs:
  - job_name: 'ml-platform'
    static_configs:
      - targets: ['ml-platform:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the provided dashboard JSON or create custom dashboards for:
- Request rate and latency
- Error rates
- Database connections
- Cache hit rates
- Authentication metrics

### Logging

Configure centralized logging:

```bash
# Using CloudWatch
aws logs create-log-group --log-group-name /ml-platform/app

# Using ELK Stack
# Configure Filebeat to ship logs to Elasticsearch
```

## SSL/TLS Setup

### Using Let's Encrypt

```bash
# Install certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d your-domain.com

# Auto-renewal
certbot renew --dry-run
```

### Using AWS Certificate Manager

```bash
# Request certificate
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS
```

## Health Checks

Configure health checks for load balancers:

- **Endpoint**: `/health`
- **Expected Status**: 200
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy Threshold**: 2
- **Unhealthy Threshold**: 3

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Kubernetes
kubectl scale deployment ml-platform --replicas=5 -n ml-platform

# Auto-scaling (Kubernetes)
kubectl autoscale deployment ml-platform \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n ml-platform
```

### Vertical Scaling

Adjust resource limits in deployment configuration based on monitoring data.

## Backup and Disaster Recovery

### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump -h <host> -U ml_platform_user ml_platform | \
  gzip > /backups/ml_platform_$(date +\%Y\%m\%d).sql.gz
```

### Application State

- User sessions: Stored in Redis (ephemeral)
- File uploads: Stored in S3 (versioned)
- Database: Regular backups with point-in-time recovery

### Disaster Recovery Plan

1. Database: Restore from latest backup
2. Application: Deploy from container registry
3. Configuration: Restore from version control
4. RTO: < 1 hour
5. RPO: < 24 hours

## Rollback Procedure

### Docker

```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker pull your-registry/ml-platform:v0.9.0
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/ml-platform -n ml-platform

# Rollback to specific revision
kubectl rollout undo deployment/ml-platform --to-revision=2 -n ml-platform
```

## Security Checklist

- [ ] All secrets stored in secure vault (AWS Secrets Manager, HashiCorp Vault)
- [ ] HTTPS/TLS enabled with valid certificates
- [ ] Database connections encrypted
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Regular security updates applied
- [ ] Vulnerability scanning enabled
- [ ] Access logs enabled
- [ ] Firewall rules configured

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Check database connection
docker-compose exec app python -c "from src.shared.database import engine; engine.connect()"
```

### High memory usage

```bash
# Check container stats
docker stats

# Adjust resource limits in docker-compose.yml or k8s manifests
```

### Database connection issues

```bash
# Test connection
psql -h <host> -U ml_platform_user -d ml_platform

# Check connection pool
docker-compose exec app python -c "from src.shared.database import engine; print(engine.pool.status())"
```

## Performance Optimization

1. **Database**:
   - Add indexes for frequently queried columns
   - Enable connection pooling
   - Use read replicas for read-heavy workloads

2. **Caching**:
   - Cache frequently accessed data in Redis
   - Set appropriate TTLs
   - Implement cache warming strategies

3. **Application**:
   - Enable async workers
   - Use connection pooling
   - Optimize database queries

## Support

For deployment issues:
- Check logs: `docker-compose logs` or `kubectl logs`
- Review health endpoint: `/health`
- Check metrics: `/metrics`
- GitHub Issues: [repository-url]/issues
