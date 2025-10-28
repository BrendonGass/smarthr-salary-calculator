# GitHub Repository Setup Guide

This guide will help you set up the SmartOffer project on GitHub and deploy it.

## Prerequisites

- Git installed on your machine
- GitHub account
- Code editor (VS Code recommended)

## Initial Setup

### 1. Commit Your Changes

First, add all the necessary files to git:

```bash
# Add all tracked and untracked files
git add .

# Commit changes
git commit -m "Initial commit: Rand Water Salary Calculator with Docker support, financial year tracking, and archive functionality"
```

### 2. Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click "New repository"
3. Repository name: `SmartOffer` or `randwater-salary-calculator`
4. Description: "Rand Water Salary Calculator with TCTC Modeling"
5. Choose Private (recommended for internal use)
6. DO NOT initialize with README, .gitignore, or license (we already have these)

### 3. Connect Local Repository to GitHub

Replace `YOUR_USERNAME` and `REPO_NAME` with your actual details:

```bash
# Add remote origin
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### 4. Verify Upload

Go to your GitHub repository URL and verify all files are uploaded.

## Files Already Configured

- ✅ `.gitignore` - Excludes sensitive data, temporary files, and uploaded files
- ✅ `README.md` - Project documentation
- ✅ `DEPLOYMENT.md` - Deployment instructions
- ✅ `Dockerfile` - Docker container configuration
- ✅ `docker-compose.yml` - Multi-container setup
- ✅ `.dockerignore` - Docker build exclusions
- ✅ `.github/workflows/deploy.yml` - CI/CD automation
- ✅ `render.yaml` - Render.com deployment config

## Important Notes

### Sensitive Data Excluded
The following sensitive files are excluded from git:
- `employee_access.json`
- `employee_packages.json`
- `submitted_packages.json`
- `sap_uploads.json`
- `system_users.json`
- `randwater_data.db`
- `uploads/*.xlsx` (uploaded files)

### Environment Variables
For production deployment, set these environment variables:

```bash
FLASK_APP=randwater_calculator.py
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### Docker Deployment

#### Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

#### Using Docker
```bash
# Build image
docker build -t randwater-calculator .

# Run container
docker run -d -p 5001:5001 randwater-calculator
```

### Deploy to Cloud

#### Option 1: Render.com (Free Tier Available)
1. Push code to GitHub
2. Go to [Render](https://render.com)
3. Connect GitHub repository
4. Deploy as web service
5. Render will automatically use `render.yaml`

#### Option 2: Heroku
```bash
# Install Heroku CLI and login
heroku create randwater-calculator
git push heroku main
```

#### Option 3: AWS Elastic Beanstalk
```bash
eb init
eb create randwater-env
eb deploy
```

## Continuous Deployment

GitHub Actions workflow (`.github/workflows/deploy.yml`) will:
- Run on every push to `main` branch
- Build Docker image
- Test the container
- Validate the application

## Branch Protection

Recommended branch protection rules:
1. Go to repository Settings > Branches
2. Add rule for `main` branch
3. Require pull request reviews before merging
4. Require status checks to pass

## Collaboration

### Adding Team Members
1. Go to repository Settings > Collaborators
2. Add team members
3. Set appropriate permissions (Admin/Write/Read)

### Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# After review and approval, merge to main
```

## Updates and Maintenance

### Pull Latest Changes
```bash
git pull origin main
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Database Migrations
When making database schema changes:
1. Create migration script
2. Backup existing database
3. Run migration
4. Test thoroughly
5. Commit and deploy

## Support

For issues or questions:
- Create an issue on GitHub
- Contact development team

## License

Proprietary - Rand Water Internal Use Only

