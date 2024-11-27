from web3 import Web3
from eth_account import Account
from cryptography.fernet import Fernet
import os
from models import WalletConfig, db

class WalletManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
        encryption_key = os.environ.get('WALLET_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("WALLET_ENCRYPTION_KEY environment variable is not set")
        try:
            self.fernet = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {str(e)}")
        
    def create_wallet(self):
        """Create a new wallet and store encrypted private key"""
        try:
            # Check if wallet already exists
            existing_wallet = WalletConfig.query.first()
            if existing_wallet:
                return existing_wallet.address
            
            # Create new wallet
            account = Account.create()
            encrypted_key = self.fernet.encrypt(account.key.hex().encode())
            
            wallet_config = WalletConfig(
                address=account.address,
                encrypted_key=encrypted_key.decode()
            )
            
            db.session.add(wallet_config)
            db.session.commit()
            return account.address
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create wallet: {str(e)}")
        
    def get_wallet(self):
        """Retrieve wallet configuration"""
        try:
            wallet_config = WalletConfig.query.first()
            if not wallet_config:
                return None
                
            encrypted_key = wallet_config.encrypted_key.encode()
            private_key = self.fernet.decrypt(encrypted_key).decode()
            return Account.from_key(private_key)
        except Exception as e:
            print(f"Error retrieving wallet: {str(e)}")
            return None
        
    def get_balance(self):
        """Get wallet AVAX balance"""
        try:
            wallet = self.get_wallet()
            if not wallet:
                return 0
            balance = self.w3.eth.get_balance(wallet.address)
            return float(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            print(f"Error getting balance: {str(e)}")
            return 0
        
    def sign_transaction(self, transaction_data):
        """Sign a transaction with the wallet's private key"""
        wallet = self.get_wallet()
        if not wallet:
            raise Exception("No wallet configured")
            
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction_data,
            wallet.key
        )
        return signed_txn
