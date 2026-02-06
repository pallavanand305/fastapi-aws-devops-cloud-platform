# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the ML Workflow Orchestration Platform.

## Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Workflows](#workflows)
- [Environment Setup](#environment-setup)
- [Deployment Process](#deployment-process)
- [Security Scanning](#security-scanning)
- [Monitoring and Alerts](#monitoring-and-alerts)

## Overview

The platform uses GitHub Actions for CI/CD automation, providing:

- **Automated Testing**: Unit, integration, and property-based tests
- **Code Quality Gates**: Linting, formatting, type checking
- **Security Scanning**: Dependency, SAST, container, and secret scanning
- **Docker Image Building**: Multi-stage builds with caching
- **Automated Deployment**: Staging and production deployments
- **Monitoring**: Test coverage, security reports, deployment status

## Pipeline Architecture

```mermaid
graph TB
    A[Code Push/PR] --> B[Code Quality Checks]
    A --> C[Run Tests]
    B --> D{Quality Pass?}
    C --> E{Tests Pass?}
    D -->|Yes| F[Build Docker Image]
    E -->|Yes| F
    D -->|No| G[Fail Build]
    E -->|No| G
    F --> H[Security Scan Image]
    H --> I{On Main Branch?}
    I -->|Yes| J[Deploy to Staging]
    I -->|No| K[End]
    J --> L[Run Smoke Tests]
    L --> M{Manual Approval}
    M -->|Approved| N[Deploy to Production]
    M -->|Rejected| K
    N --> O[Run Smoke Tests]
    O --> P[Notify Team]
```

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

Main pipeline that runs on every push and pull request.

#### Jobs

##### Code Quality Checks

Runs code quality and security checks:

```yaml
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)
- MyPy (type checking)
- Bandit (security scanning)
- Safety (dependency vulnerabilities)
```

**Triggers**: All pushes and PRs  
**Duration**: ~2-3 minutes  
**Failure Action**: Blocks merge

##### Run Tests

Executes comprehensive test suite:

```yaml
Services:
  - PostgreSQL 15
  - Redis 7

Test Types:
  - Unit tests
  - Integration tests
  - Property-based tests (Hypothesis)

Coverage:
  - Minimum: 70%
  - Target: 80%+
  - Reports: Codecov, HTML, XML
```

**Triggers**: All pushes and PRs  
**Duration**: ~5-10 minutes  
**Failure Action**: Blocks merge

##### Build Docker Image

Builds and pushes Docker images:

```yaml
Registry: GitHub Container Registry (ghcr.io)
Tags:
  - Branch name (e.g., main, develop)
  - PR number (e.g., pr-123)
  - Git SHA (e.g., main-abc1234)
  - Semantic version (e.g., v1.2.3)
  - latest (main branch only)

Features:
  - Multi-stage builds
  - Layer caching
  - Trivy vulnerability scanning
```

**Triggers**: Push to main/develop  
**Duration**: ~5-8 minutes  
**Failure Action**: Alerts team

##### Deploy to Staging

Deploys to staging environment:

```yaml
Environment: staging
URL: https://staging.ml-platform.example.com
Kubernetes Cluster: ml-platform-staging
Region: us-east-1

Steps:
  1. Configure AWS credentials
  2. Update kubeconfig
  3. Deploy with Helm/kubectl
  4. Run smoke tests
```

**Triggers**: Push to main branch  
**Duration**: ~3-5 minutes  
**Failure Action**: Rollback, alert team

##### Deploy to Production

Deploys to production with manual approval:

```yaml
Environment: production
URL: https://ml-platform.example.com
Kubernetes Cluster: ml-platform-production
Region: us-east-1
Approval: Required

Steps:
  1. Manual approval gate
  2. Configure AWS credentials
  3. Update kubeconfig
  4. Deploy with Helm/kubectl
  5. Run smoke tests
  6. Notify team
```

**Triggers**: After staging deployment  
**Duration**: ~3-5 minutes  
**Failure Action**: Rollback, alert team

### 2. Security Scanning (`.github/workflows/security-scan.yml`)

Comprehensive security scanning workflow.

#### Jobs

##### Dependency Vulnerability Scan

Scans Python dependencies for known vulnerabilities:

```yaml
Tools:
  - Safety: Checks against safety-db
  - pip-audit: Checks against OSV database

Output:
  - JSON reports
  - Severity ratings
  - Remediation advice
```

**Triggers**: Daily at 2 AM UTC, push to main  
**Duration**: ~2-3 minutes

##### SAST (Static Application Security Testing)

Static code analysis for security issues:

```yaml
Tools:
  - Bandit: Python security linter
  - Semgrep: Pattern-based security scanner

Checks:
  - SQL injection
  - XSS vulnerabilities
  - Hardcoded secrets
  - Insecure crypto
  - Command injection
```

**Triggers**: Daily, push to main  
**Duration**: ~3-5 minutes

##### CodeQL Analysis

GitHub's semantic code analysis:

```yaml
Language: Python
Queries: security-and-quality
Features:
  - Data flow analysis
  - Control flow analysis
  - Taint tracking
  - Custom queries
```

**Triggers**: Daily, push to main  
**Duration**: ~5-10 minutes

##### Secret Scanning

Detects exposed secrets in code:

```yaml
Tools:
  - Gitleaks: Fast secret scanner
  - TruffleHog: Deep secret scanner

Detects:
  - API keys
  - Passwords
  - Private keys
  - Tokens
  - Certificates
```

**Triggers**: Daily, push to main  
**Duration**: ~2-3 minutes

##### Container Image Scanning

Scans Docker images for vulnerabilities:

```yaml
Tool: Trivy
Scans:
  - OS packages
  - Application dependencies
  - Misconfigurations
  - Secrets in layers

Severity: CRITICAL, HIGH
Output: SARIF, Table
```

**Triggers**: Daily, push to main  
**Duration**: ~3-5 minutes

##### License Compliance Check

Verifies dependency licenses:

```yaml
Tool: pip-licenses
Output:
  - JSON report
  - Markdown table

Checks:
  - License compatibility
  - Copyleft licenses
  - Unknown licenses
```

**Triggers**: Daily, push to main  
**Duration**: ~1-2 minutes

## Environment Setup

### Required Secrets

Configure these secrets in GitHub repository settings:

#### AWS Credentials

```yaml
AWS_ACCESS_KEY_ID: AWS access key for deployments
AWS_SECRET_ACCESS_KEY: AWS secret key for deployments
```

#### Container Registry

```yaml
GITHUB_TOKEN: Automatically provided by GitHub Actions
```

#### Optional Secrets

```yaml
CODECOV_TOKEN: For Codecov integration
SLACK_WEBHOOK: For Slack notifications
PAGERDUTY_TOKEN: For PagerDuty alerts
GITLEAKS_LICENSE: For Gitleaks Pro features
```

### Environment Variables

#### Test Environment

```yaml
DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
REDIS_URL: redis://localhost:6379/0
SECRET_KEY: test-secret-key-for-ci
HYPOTHESIS_PROFILE: ci
```

#### Staging Environment

```yaml
ENVIRONMENT: staging
DATABASE_URL: <staging-db-url>
REDIS_URL: <staging-redis-url>
SECRET_KEY: <staging-secret>
```

#### Production Environment

```yaml
ENVIRONMENT: production
DATABASE_URL: <production-db-url>
REDIS_URL: <production-redis-url>
SECRET_KEY: <production-secret>
```

### GitHub Environments

Configure environments in repository settings:

#### Staging

```yaml
Name: staging
URL: https://staging.ml-platform.example.com
Protection Rules:
  - Wait timer: 0 minutes
  - Required reviewers: 0
Secrets:
  - AWS credentials
  - Database credentials
```

#### Production

```yaml
Name: production
URL: https://ml-platform.example.com
Protection Rules:
  - Wait timer: 5 minutes
  - Required reviewers: 2
  - Restrict to main branch
Secrets:
  - AWS credentials
  - Database credentials
```

## Deployment Process

### Staging Deployment

Automatic deployment on push to main:

```bash
1. Code merged to main branch
2. CI/CD pipeline runs
3. Tests pass
4. Docker image built
5. Image pushed to registry
6. Kubernetes deployment updated
7. Smoke tests run
8. Team notified
```

### Production Deployment

Manual approval required:

```bash
1. Staging deployment successful
2. Manual approval requested
3. Reviewer approves deployment
4. Kubernetes deployment updated
5. Smoke tests run
6. Team notified
7. Monitoring alerts configured
```

### Rollback Process

If deployment fails:

```bash
# Automatic rollback
kubectl rollout undo deployment/ml-platform -n production

# Manual rollback to specific version
kubectl rollout undo deployment/ml-platform -n production --to-revision=2

# Check rollout status
kubectl rollout status deployment/ml-platform -n production
```

### Blue-Green Deployment

For zero-downtime deployments:

```bash
1. Deploy new version (green)
2. Run health checks
3. Switch traffic to green
4. Monitor for issues
5. Keep blue for rollback
6. Decommission blue after validation
```

## Security Scanning

### Vulnerability Management

#### Severity Levels

- **CRITICAL**: Immediate action required
- **HIGH**: Fix within 7 days
- **MEDIUM**: Fix within 30 days
- **LOW**: Fix in next release

#### Response Process

```bash
1. Vulnerability detected
2. Security team notified
3. Impact assessment
4. Patch/mitigation applied
5. Verification testing
6. Deployment
7. Documentation updated
```

### Security Reports

Reports are uploaded as artifacts:

- `bandit-security-report`: Python security issues
- `semgrep-report`: Pattern-based security findings
- `trivy-container-report`: Container vulnerabilities
- `safety-report`: Dependency vulnerabilities
- `pip-audit-report`: Package vulnerabilities
- `licenses`: License compliance report

### SARIF Integration

Security findings are uploaded to GitHub Security:

```yaml
Location: Security > Code scanning alerts
Format: SARIF (Static Analysis Results Interchange Format)
Tools:
  - Bandit
  - Semgrep
  - CodeQL
  - Trivy
```

## Monitoring and Alerts

### Test Coverage

- **Codecov**: Automatic coverage tracking
- **Threshold**: 70% minimum (CI gate)
- **Trend**: Track coverage over time
- **Reports**: HTML, XML, terminal

### Build Status

- **GitHub Status Checks**: Required for merge
- **Branch Protection**: Enforce passing tests
- **Status Badge**: Display in README

### Deployment Status

- **Kubernetes Events**: Monitor pod status
- **Health Checks**: Automatic endpoint checks
- **Smoke Tests**: Post-deployment validation

### Notifications

Configure notifications for:

- **Build Failures**: Slack, email
- **Security Alerts**: PagerDuty, email
- **Deployment Success**: Slack
- **Deployment Failure**: PagerDuty, Slack, email

## Best Practices

### 1. Branch Strategy

```bash
main: Production-ready code
develop: Integration branch
feature/*: Feature branches
hotfix/*: Emergency fixes
```

### 2. Commit Messages

```bash
Format: <type>(<scope>): <subject>

Types:
  - feat: New feature
  - fix: Bug fix
  - docs: Documentation
  - test: Tests
  - refactor: Code refactoring
  - chore: Maintenance

Example: feat(auth): add JWT token refresh endpoint
```

### 3. Pull Requests

- **Required**: Passing CI checks
- **Reviews**: At least 1 approval
- **Tests**: Add tests for new features
- **Documentation**: Update relevant docs

### 4. Testing

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Property Tests**: Test universal properties
- **Coverage**: Maintain 80%+ coverage

### 5. Security

- **Secrets**: Never commit secrets
- **Dependencies**: Keep dependencies updated
- **Scanning**: Review security reports
- **Patches**: Apply security patches promptly

### 6. Deployment

- **Staging First**: Always deploy to staging
- **Smoke Tests**: Verify critical paths
- **Monitoring**: Watch metrics post-deployment
- **Rollback Plan**: Have rollback procedure ready

## Troubleshooting

### Common Issues

#### 1. Test Failures

```bash
# Check test logs
gh run view <run-id> --log

# Run tests locally
make test-ci

# Debug specific test
pytest tests/test_file.py::test_function -vv
```

#### 2. Build Failures

```bash
# Check build logs
docker build -t test .

# Verify Dockerfile
docker build --no-cache -t test .

# Check dependencies
pip install -r requirements.txt
```

#### 3. Deployment Failures

```bash
# Check pod status
kubectl get pods -n production

# Check pod logs
kubectl logs <pod-name> -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

#### 4. Security Scan Failures

```bash
# Review security report
gh run view <run-id> --log

# Check specific vulnerability
safety check --json | jq '.vulnerabilities'

# Update dependencies
pip install --upgrade <package>
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)

## Support

For CI/CD questions or issues:

1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check team wiki for runbooks
4. Contact DevOps team
