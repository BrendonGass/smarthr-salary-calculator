#!/bin/bash
set -e

echo "=== Randwater Calculator Docker Entrypoint ==="

# Initialize JSON files - remove if directory, create if doesn't exist
initialize_json_file() {
    local file=$1
    local default_value=$2
    
    # If it's a directory, remove it
    if [ -d "$file" ]; then
        echo "Removing directory $file..."
        rm -rf "$file"
    fi
    
    # If file doesn't exist or is empty, initialize it
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        echo "Initializing $file..."
        echo "$default_value" > "$file"
    fi
}

# Initialize all JSON data files with proper structure
initialize_json_file "employee_access.json" '{}'
initialize_json_file "employee_packages.json" '{}'
initialize_json_file "randwater_package_audit.json" '[]'
initialize_json_file "submitted_packages.json" '[]'
initialize_json_file "sap_uploads.json" '[]'
initialize_json_file "system_logs.json" '[]'
initialize_json_file "system_users.json" '[]'
initialize_json_file "password_reset_tokens.json" '{}'
initialize_json_file "randwater_notifications.json" '[]'
initialize_json_file "email_logs.json" '[]'
initialize_json_file "package_audit.json" '[]'
initialize_json_file "salary_simulations.json" '[]'

# Check if pension_config.json exists, if not copy from static
if [ ! -f "pension_config.json" ] && [ -f "static/pension_config.json" ]; then
    echo "Copying pension_config.json from static/..."
    cp static/pension_config.json pension_config.json
fi

# Create a simple default pension config if it doesn't exist
if [ ! -f "pension_config.json" ]; then
    echo "Creating default pension_config.json..."
    cat > pension_config.json << 'EOF'
{
  "pensionContributions": {
    "employee": 7.5,
    "employer": 15.0
  },
  "groupLifeRates": {
    "default": 1.5
  }
}
EOF
fi

# Ensure directories exist with proper permissions
mkdir -p uploads backups drafts
chmod 755 uploads backups drafts

echo "=== Initialization complete ==="
echo "Starting application..."

# Execute the CMD from Dockerfile
exec "$@"

