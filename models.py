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
