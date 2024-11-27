from app import db
from datetime import datetime

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(66), unique=True, nullable=False)
    type = db.Column(db.String(32), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False)
    gas_used = db.Column(db.Float)
    details = db.Column(db.JSON)

class WalletConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class AIDecision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    decision_type = db.Column(db.String(32), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    reasoning = db.Column(db.Text)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))


class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(32), nullable=False)  # user_preference, transaction_pattern, conversation, command_pattern
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.JSON, nullable=False)
    confidence = db.Column(db.Float, default=1.0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('memory_type', 'key', name='unique_memory_type_key'),
    )