import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the salary calculator application"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # SAP Integration settings
    SAP_BASE_URL = os.environ.get('SAP_BASE_URL') or 'https://your-sap-system.com'
    SAP_USERNAME = os.environ.get('SAP_USERNAME') or 'your_username'
    SAP_PASSWORD = os.environ.get('SAP_PASSWORD') or 'your_password'
    SAP_CLIENT = os.environ.get('SAP_CLIENT') or '100'
    
    # ESS Integration settings
    ESS_VALIDATION_URL = os.environ.get('ESS_VALIDATION_URL') or 'https://your-ess-system.com/validate-token'
    ESS_API_KEY = os.environ.get('ESS_API_KEY') or 'your_ess_api_key'
    
    # File storage settings
    EXPORT_DIR = os.environ.get('EXPORT_DIR') or 'exports'
    UPLOAD_DIR = os.environ.get('UPLOAD_DIR') or 'uploads'
    
    # Tax settings file
    TAX_SETTINGS_FILE = os.environ.get('TAX_SETTINGS_FILE') or 'tax_settings.json'
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'
    
    @classmethod
    def get_sap_config(cls):
        """Get SAP configuration dictionary"""
        return {
            'base_url': cls.SAP_BASE_URL,
            'username': cls.SAP_USERNAME,
            'password': cls.SAP_PASSWORD,
            'client': cls.SAP_CLIENT
        }
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        # Create necessary directories
        os.makedirs(cls.EXPORT_DIR, exist_ok=True)
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        
        # Set up logging
        import logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 