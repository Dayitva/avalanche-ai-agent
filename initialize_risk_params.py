from base_models import RiskParameter, db
from flask import Flask
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('WALLET_ENCRYPTION_KEY', 'dev-key')
    return app

def initialize_risk_parameters():
    """Initialize default risk parameters"""
    try:
        # Check if parameters already exist
        if RiskParameter.query.first() is None:
            default_parameters = [
                {
                    'parameter_type': 'max_slippage',
                    'value': 1.0,
                    'min_value': 0.1,
                    'max_value': 5.0,
                    'default_value': 1.0,
                    'description': 'Maximum allowed slippage percentage for trades'
                },
                {
                    'parameter_type': 'min_liquidity',
                    'value': 100000,
                    'min_value': 10000,
                    'max_value': 1000000,
                    'default_value': 100000,
                    'description': 'Minimum liquidity required in pool for trade execution'
                },
                {
                    'parameter_type': 'max_gas_multiplier',
                    'value': 1.5,
                    'min_value': 1.0,
                    'max_value': 3.0,
                    'default_value': 1.5,
                    'description': 'Maximum multiplier for gas price estimation'
                },
                {
                    'parameter_type': 'min_profit_threshold',
                    'value': 0.5,
                    'min_value': 0.1,
                    'max_value': 5.0,
                    'default_value': 0.5,
                    'description': 'Minimum profit percentage required for trade execution'
                },
                {
                    'parameter_type': 'max_exposure_percentage',
                    'value': 20.0,
                    'min_value': 1.0,
                    'max_value': 100.0,
                    'default_value': 20.0,
                    'description': 'Maximum percentage of portfolio to risk in a single trade'
                }
            ]

            for param in default_parameters:
                risk_param = RiskParameter(**param)
                db.session.add(risk_param)

            db.session.commit()
            print("Default risk parameters initialized successfully")
        else:
            print("Risk parameters already initialized")

    except Exception as e:
        print(f"Error initializing risk parameters: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        initialize_risk_parameters()
