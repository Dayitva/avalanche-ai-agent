from app import app
from wallet_manager import WalletManager
import os
import sys

def initialize_wallet():
    """Initialize wallet if one doesn't exist"""
    try:
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

if __name__ == "__main__":
    # Ensure required environment variables are set
    required_vars = ['WALLET_ENCRYPTION_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)
    
    # Ensure database tables exist
    try:
        with app.app_context():
            from app import db
            import models
            db.create_all()
    except Exception as e:
        print(f"Error creating database tables: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize wallet
    if not initialize_wallet():
        print("Failed to initialize wallet", file=sys.stderr)
        sys.exit(1)
    
    # Set default port to 5000 and bind to all interfaces
    port = int(os.environ.get("PORT", 5000))
    
    # Start the Flask application
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False  # Disable debug mode in production
    )
