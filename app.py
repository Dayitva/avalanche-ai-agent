import os
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from base_models import db

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "avalanche-ai-agent-key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Import components after db initialization
from wallet_manager import WalletManager
from chain_scanner import ChainScanner
from decision_engine import DecisionEngine
from transaction_executor import TransactionExecutor

# Global component variables
wallet_manager = None
chain_scanner = None
decision_engine = None
transaction_executor = None

def init_components():
    """Initialize components within application context"""
    global wallet_manager, chain_scanner, decision_engine, transaction_executor
    
    # Import here to avoid circular imports
    from wallet_manager import WalletManager
    from chain_scanner import ChainScanner
    from decision_engine import DecisionEngine
    from transaction_executor import TransactionExecutor
    from base_models import Chain
    
    try:
        # Initialize with default chain (Avalanche C-Chain)
        default_chain = Chain.query.filter_by(name='Avalanche C-Chain', active=True).first()
        if not default_chain:
            raise ValueError("Default chain not found")
            
        wallet_manager = WalletManager(default_chain.id)
        chain_scanner = ChainScanner(default_chain.id)
        decision_engine = DecisionEngine()
        transaction_executor = TransactionExecutor(wallet_manager)
        
        print("Components initialized successfully")
    except Exception as e:
        print(f"Error initializing components: {str(e)}")
        raise

# Add route to get supported chains
@app.route('/api/chains')
def get_chains():
    from base_models import Chain
    chains = Chain.query.filter_by(active=True).all()
    return jsonify([{
        'id': chain.id,
        'name': chain.name,
        'network_id': chain.network_id,
        'symbol': chain.symbol,
        'explorer_url': chain.explorer_url
    } for chain in chains])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

@app.route('/api/wallet/balance')
@app.route('/api/wallet/balance/<int:chain_id>')
def get_balance(chain_id=None):
    if not wallet_manager:
        return jsonify({"error": "Wallet manager not initialized"}), 500
    
    try:
        original_chain_id = wallet_manager.chain_id
        try:
            if chain_id is not None:
                wallet_manager.switch_chain(chain_id)
            balance = wallet_manager.get_balance()
            current_chain = wallet_manager.chain
            return jsonify({
                "balance": balance,
                "chain_id": current_chain.id,
                "symbol": current_chain.symbol,
                "network_id": current_chain.network_id
            })
        finally:
            if chain_id is not None:
                wallet_manager.switch_chain(original_chain_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/wallet/chains')
def get_supported_chains():
    if not wallet_manager:
        return jsonify({"error": "Wallet manager not initialized"}), 500
    
    chains = WalletManager.get_supported_chains()
    return jsonify(chains)

@app.route('/api/transactions/recent')
def get_recent_transactions():
    from base_models import Transaction
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    return jsonify([{
        'hash': tx.hash,
        'type': tx.type,
        'amount': tx.amount,
        'timestamp': tx.timestamp.isoformat(),
        'status': tx.status,
        'chain_id': tx.chain_id
    } for tx in transactions])

def run_ai_cycle():
    """Execute one cycle of the AI agent's decision-making process across all chains"""
    if not all([chain_scanner, decision_engine, transaction_executor]):
        print("Components not initialized")
        return

    try:
        # Get all active chains
        from base_models import Chain
        active_chains = Chain.query.filter_by(active=True).all()
        
        for chain in active_chains:
            try:
                # Switch to current chain
                chain_scanner.switch_chain(chain.id)
                transaction_executor.switch_chain(chain.id)
                
                # Scan chain data
                chain_data = chain_scanner.scan_latest_data()
                
                # Get AI decision
                decision = decision_engine.make_decision(chain_data)
                
                # Execute transaction if needed
                if decision.should_execute:
                    transaction_executor.execute_transaction(decision.transaction_data)
                    
            except Exception as chain_error:
                print(f"Error processing chain {chain.name}: {str(chain_error)}")
                continue
            
    except Exception as e:
        print(f"Error in AI cycle: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_ai_cycle, 'interval', minutes=5)
scheduler.start()

with app.app_context():
    from base_models import *  # Import all models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
