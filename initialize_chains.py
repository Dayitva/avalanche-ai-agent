from flask import current_app
from base_models import Chain, db

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
        raise

if __name__ == "__main__":
    try:
        # When run directly, create app context
        from app import app
        with app.app_context():
            initialize_default_chains()
    except Exception as e:
        print(f"Failed to initialize chains: {str(e)}")
        exit(1)
