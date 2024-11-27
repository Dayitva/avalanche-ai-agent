import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
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

# Initialize components
wallet_manager = WalletManager()
chain_scanner = ChainScanner()
decision_engine = DecisionEngine()
transaction_executor = TransactionExecutor(wallet_manager)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

@app.route('/api/wallet/balance')
def get_balance():
    balance = wallet_manager.get_balance()
    return jsonify({"balance": balance})

@app.route('/api/transactions/recent')
def get_recent_transactions():
    from models import Transaction
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    return jsonify([{
        'hash': tx.hash,
        'type': tx.type,
        'amount': tx.amount,
        'timestamp': tx.timestamp.isoformat(),
        'status': tx.status
    } for tx in transactions])

def run_ai_cycle():
    """Execute one cycle of the AI agent's decision-making process"""
    try:
        # Scan chain data
        chain_data = chain_scanner.scan_latest_data()
        
        # Get AI decision
        decision = decision_engine.make_decision(chain_data)
        
        # Execute transaction if needed
        if decision.should_execute:
            transaction_executor.execute_transaction(decision.transaction_data)
            
    except Exception as e:
        print(f"Error in AI cycle: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_ai_cycle, 'interval', minutes=5)
scheduler.start()

with app.app_context():
    import models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
