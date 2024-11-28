import os
import sys
from flask import Flask
from base_models import db, init_db
from initialize_chains import initialize_default_chains

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('WALLET_ENCRYPTION_KEY', 'dev-key')
    init_db(app)
    return app

def initialize_wallet(app):
    """Initialize wallet if one doesn't exist"""
    try:
        from wallet_manager import WalletManager
        with app.app_context():
            wallet_manager = WalletManager()
            if not wallet_manager.get_wallet():
                address = wallet_manager.create_wallet()
                print(f"Created new wallet with address: {address}")
                return True
            return True
    except Exception as e:
        print(f"Error initializing wallet: {str(e)}", file=sys.stderr)
        return False

def init_components(app):
    """Initialize all components"""
    from app import init_app_components
    with app.app_context():
        return init_app_components()

if __name__ == "__main__":
    # Ensure required environment variables are set
    required_vars = ['WALLET_ENCRYPTION_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create and configure Flask app
        app = create_app()
        
        with app.app_context():
            # Initialize chains
            initialize_default_chains()
            
            # Initialize wallet
            if not initialize_wallet(app):
                print("Failed to initialize wallet", file=sys.stderr)
                sys.exit(1)
            
            # Initialize components
            if not init_components(app):
                print("Failed to initialize components", file=sys.stderr)
                sys.exit(1)
        
        # Import routes after initialization
        from app import configure_routes
        configure_routes(app)
        
        # Set default port to 5000 and bind to all interfaces
        port = int(os.environ.get("PORT", 5000))
        
        # Start the Flask application
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False  # Disable debug mode in production
        )
            
    except Exception as e:
        print(f"Error during initialization: {str(e)}", file=sys.stderr)
        sys.exit(1)
