from web3 import Web3
from eth_account import Account
from cryptography.fernet import Fernet
import os
from base_models import WalletConfig, db

class WalletManager:
    def __init__(self, chain_id=None):
        """Initialize wallet manager with optional chain_id"""
        self.chain_id = chain_id or self._get_default_chain_id()
        self.chain = self._get_chain_info(self.chain_id)
        self.w3 = Web3(Web3.HTTPProvider(self.chain.rpc_url))
        
        encryption_key = os.environ.get('WALLET_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("WALLET_ENCRYPTION_KEY environment variable is not set")
        try:
            self.fernet = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {str(e)}")
            
    def _get_default_chain_id(self):
        """Get the default chain ID (Avalanche C-Chain)"""
        from flask import current_app
        from base_models import Chain
        
        with current_app.app_context():
            chain = Chain.query.filter_by(name='Avalanche C-Chain', active=True).first()
            if not chain:
                raise ValueError("Default chain (Avalanche C-Chain) not found or not active")
            return chain.id
    
    @staticmethod
    def get_supported_chains():
        """Get list of supported chains"""
        from flask import current_app
        from base_models import Chain
        
        with current_app.app_context():
            chains = Chain.query.filter_by(active=True).all()
            return [{
                'id': chain.id,
                'name': chain.name,
                'network_id': chain.network_id,
                'symbol': chain.symbol
            } for chain in chains]
    
    def switch_chain(self, chain_id):
        """Switch to a different chain"""
        from flask import current_app
        
        with current_app.app_context():
            self.chain_id = chain_id
            self.chain = self._get_chain_info(chain_id)
            self.w3 = Web3(Web3.HTTPProvider(self.chain.rpc_url))
            return True
        
    def _get_chain_info(self, chain_id):
        """Get chain information from database"""
        from base_models import Chain
        chain = Chain.query.get(chain_id)
        if not chain:
            raise ValueError(f"Chain with ID {chain_id} not found")
        return chain
        
    def create_wallet(self):
        """Create a new wallet and store encrypted private key for the current chain"""
        try:
            # Check if wallet already exists for this chain
            existing_wallet = WalletConfig.query.filter_by(chain_id=self.chain_id).first()
            if existing_wallet:
                return existing_wallet.address
            
            # Create new wallet
            account = Account.create()
            encrypted_key = self.fernet.encrypt(account.key.hex().encode())
            
            wallet_config = WalletConfig(
                address=account.address,
                encrypted_key=encrypted_key.decode(),
                chain_id=self.chain_id
            )
            
            db.session.add(wallet_config)
            db.session.commit()
            return account.address
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create wallet: {str(e)}")
        
    def get_wallet(self):
        """Retrieve wallet configuration for the current chain"""
        try:
            wallet_config = WalletConfig.query.filter_by(chain_id=self.chain_id).first()
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
