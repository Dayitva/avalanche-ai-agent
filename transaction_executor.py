from web3 import Web3
from base_models import Transaction, db
from memory_manager import MemoryManager
from datetime import datetime

class TransactionExecutor:
    def __init__(self, wallet_manager):
        """Initialize transaction executor with wallet manager"""
        self.wallet_manager = wallet_manager
        self.memory_manager = MemoryManager()
        self.w3 = Web3(Web3.HTTPProvider(self.wallet_manager.chain.rpc_url))
    def switch_chain(self, chain_id):
        """Switch to a different chain"""
        self.wallet_manager.switch_chain(chain_id)
        self.w3 = Web3(Web3.HTTPProvider(self.wallet_manager.chain.rpc_url))
        
    def execute_transaction(self, transaction_data):
        """Execute a transaction based on AI decision"""
        try:
            # Prepare transaction
            tx_params = self._prepare_transaction(transaction_data)
            
            # Sign transaction
            signed_tx = self.wallet_manager.sign_transaction(tx_params)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Record transaction and update pattern confidence
            tx_hash_hex = tx_hash.hex()
            self._record_transaction(tx_hash_hex, tx_receipt, transaction_data)
            
            # Update pattern confidence on success
            pattern_key = f"{transaction_data['type']}_{datetime.utcnow().strftime('%Y%m')}"
            self.memory_manager.update_pattern_confidence('transaction_pattern', pattern_key, True)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Error executing transaction: {str(e)}")
            self._record_failed_transaction(str(e), transaction_data)
            
            # Update pattern confidence on failure
            pattern_key = f"{transaction_data['type']}_{datetime.utcnow().strftime('%Y%m')}"
            self.memory_manager.update_pattern_confidence('transaction_pattern', pattern_key, False)
            return None
            
    def _prepare_transaction(self, transaction_data):
        """Prepare transaction parameters"""
        wallet = self.wallet_manager.get_wallet()
        
        return {
            'nonce': self.w3.eth.get_transaction_count(wallet.address),
            'gasPrice': self.w3.eth.gas_price,
            'gas': self._estimate_gas(transaction_data),
            'to': Web3.to_checksum_address(transaction_data['to']),
            'value': transaction_data.get('value', 0),
            'data': transaction_data.get('data', ''),
            'chainId': self.wallet_manager.chain.network_id
        }
        
    def _estimate_gas(self, transaction_data):
        """Estimate gas for transaction"""
        try:
            return self.w3.eth.estimate_gas({
                'to': transaction_data['to'],
                'value': transaction_data.get('value', 0),
                'data': transaction_data.get('data', '')
            })
        except Exception:
            return 21000  # Default gas limit
            
    def _record_transaction(self, tx_hash, receipt, transaction_data):
        """Record successful transaction in database"""
        transaction = Transaction(
            hash=tx_hash,
            type=transaction_data['type'],
            amount=self.w3.from_wei(transaction_data.get('value', 0), 'ether'),
            status='success',
            gas_used=receipt['gasUsed'],
            details=transaction_data,
            chain_id=self.wallet_manager.chain_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
    def _record_failed_transaction(self, error, transaction_data):
        """Record failed transaction in database"""
        transaction = Transaction(
            hash='failed_' + str(db.session.query(Transaction).count() + 1),
            type=transaction_data['type'],
            amount=self.w3.from_wei(transaction_data.get('value', 0), 'ether'),
            status='failed',
            details={'error': str(error), **transaction_data},
            chain_id=self.wallet_manager.chain_id
        )
        
        db.session.add(transaction)
        db.session.commit()
