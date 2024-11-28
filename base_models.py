from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

class Chain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    network_id = db.Column(db.Integer, nullable=False)
    rpc_url = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    explorer_url = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)

class WalletConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)
    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(66), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    gas_used = db.Column(db.BigInteger)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)
    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'), nullable=False)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.JSON, nullable=False)
    confidence = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

class AIDecision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    decision_type = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    reasoning = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    abi = db.Column(db.JSON, nullable=False)
    bytecode = db.Column(db.Text, nullable=False)
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_hash = db.Column(db.String(66), nullable=False)
    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.UniqueConstraint('address', 'chain_id', name='uq_contract_address_chain'),
    )