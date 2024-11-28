from base_models import Chain, db, init_db
from flask import Flask
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('WALLET_ENCRYPTION_KEY', 'dev-key')
    init_db(app)
    return app

def initialize_default_chains():
    """Initialize default blockchain networks"""
    try:
        # Check if chains already exist
        if Chain.query.first() is None:
            # Add Avalanche C-Chain
            avalanche_c = Chain(
                name='Avalanche C-Chain',
                network_id=43114,
                rpc_url='https://api.avax.network/ext/bc/C/rpc',
                symbol='AVAX',
                explorer_url='https://snowtrace.io',
                active=True
            )
            
            # Add Avalanche FUJI (Testnet)
            avalanche_fuji = Chain(
                name='Avalanche Fuji',
                network_id=43113,
                rpc_url='https://api.avax-test.network/ext/bc/C/rpc',
                symbol='AVAX',
                explorer_url='https://testnet.snowtrace.io',
                active=True
            )
            
            db.session.add(avalanche_c)
            db.session.add(avalanche_fuji)
            db.session.commit()
            print("Default chains initialized successfully")
        else:
            print("Chains already initialized")
            
    except Exception as e:
        print(f"Error initializing default chains: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        initialize_default_chains()
