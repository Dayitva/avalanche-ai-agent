from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Chain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    network_id = db.Column(db.Integer, nullable=False)
    rpc_url = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    explorer_url = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='chain', lazy=True)
    wallet_configs = db.relationship('WalletConfig', backref='chain', lazy=True)
    
    def __repr__(self):
        return f'<Chain {self.name}>'

class WalletConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('address', 'chain_id', name='unique_address_per_chain'),
    )

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(66), unique=True, nullable=False)
    type = db.Column(db.String(32), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False)
    gas_used = db.Column(db.Float)
    details = db.Column(db.JSON)
    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'), nullable=False)
    
    # Add relationship with AIDecision
    decisions = db.relationship('AIDecision', backref='transaction', lazy=True)

class AIDecision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    decision_type = db.Column(db.String(32), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    reasoning = db.Column(db.Text)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(32), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.JSON, nullable=False)
    confidence = db.Column(db.Float, default=1.0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('memory_type', 'key', name='unique_memory_type_key'),
    )
