# SmartOffer - Rand Water Salary Calculator

A Flask-based web application for managing and calculating employee salary packages at Rand Water.

## Features

- **Employee Package Management**: Create, edit, and manage employee packages
- **Salary Calculator**: Real-time salary calculations with tax, UIF, SDL, and deductions
- **SAP Data Integration**: Upload Excel files from SAP to create employee packages
- **Package Analytics**: Comprehensive reporting and analytics dashboard
- **Payslip Generation**: Generate and print professional payslips
- **Employee Portal**: Employees can view their packages and payslips
- **Admin Dashboard**: Full admin management interface
- **Audit Trail**: Complete system change logging

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for containerized deployment)
- Git

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd SmartOffer
   ```

2. **Build and start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Application: http://localhost:5001
   - Admin Panel: http://localhost:5001/admin/randwater
   - Employee Login: http://localhost:5001/employee/login

### Using Python (Development)

1. **Clone and navigate to the project**
   ```bash
   git clone <your-repo-url>
   cd SmartOffer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run_randwater.py
   ```

5. **Access the application**
   - Application: http://localhost:5001

## Configuration

### Environment Variables

The application uses the following environment variables (set in Docker or as system variables):

- `FLASK_APP`: Application entry point (default: `randwater_calculator.py`)
- `FLASK_ENV`: Environment mode (`development` or `production`)
- `PYTHONUNBUFFERED`: Python output buffering (set to `1`)

### Database

The application uses SQLite by default. Database files are stored locally:
- `randwater_data.db`: Main database

### Data Files

JSON configuration files (should be created on first run):
- `employee_access.json`: Employee access permissions
- `employee_packages.json`: Employee package data
- `submitted_packages.json`: Submitted package records
- `randwater_package_audit.json`: Audit trail logs
- `system_logs.json`: System activity logs
- `system_users.json`: User management data
- `pension_config.json`: Pension configuration
- `salary_simulations.json`: Salary simulation data

## Deployment

### Docker Deployment

The application is configured for Docker deployment:

```bash
# Build the image
docker build -t randwater-calculator .

# Run the container
docker run -d \
  -p 5001:5001 \
  -v $(pwd)/randwater_data.db:/app/randwater_data.db \
  -v $(pwd)/employee_access.json:/app/employee_access.json \
  --name randwater-app \
  randwater-calculator

# Or use docker-compose
docker-compose up -d
```

### Production Deployment

For production deployment:

1. **Use Gunicorn** (already configured in Dockerfile)
2. **Set up a reverse proxy** (Nginx recommended)
3. **Configure SSL certificates**
4. **Set up proper database backups**
5. **Configure environment variables for production**

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Project Structure

```
SmartOffer/
├── app.py                      # Legacy application entry
├── randwater_calculator.py     # Main Flask application
├── run_randwater.py           # Application runner
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── .dockerignore              # Docker build exclusions
├── .gitignore                 # Git exclusions
├── config.py                   # Configuration file
├── models.py                   # Database models
├── database.py                 # Database utilities
├── db_models.py               # Database models (alternative)
├── static/                     # Static files (CSS, images)
│   ├── style.css
│   ├── images/
│   └── icons/
├── templates/                  # HTML templates
│   ├── admin templates
│   ├── employee templates
│   └── login templates
└── backups/                    # Database backups
```

## Key Features

### Package Management
- Create and edit employee packages
- Bulk package operations
- Package submission workflow
- Draft management

### Salary Calculator
- Real-time calculations
- Tax brackets and deductions
- UIF and SDL calculations
- Medical aid and pension contributions

### Reporting
- Package analytics dashboard
- Payslip reports
- Tax reports
- Variance analysis
- Audit trail

### Employee Portal
- View personal package
- View payslip
- Submit feedback

## Development

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test
3. Commit changes: `git commit -m "Add new feature"`
4. Push and create pull request

### Running Tests

Currently, manual testing is used. Automated test suite to be added.

## Troubleshooting

### Port Already in Use
If port 5001 is already in use, change the port in:
- `docker-compose.yml` (ports section)
- `run_randwater.py` (port parameter)

### Database Issues
- Check if `randwater_data.db` exists
- Ensure write permissions
- Check for database locks

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Activate virtual environment
- Check Python version (requires 3.9+)

## Support

For issues and questions, please contact the development team.

## License

Proprietary - Rand Water Internal Use Only

## Version

Current Version: 1.0
