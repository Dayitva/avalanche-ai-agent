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
        """Execute a transaction based on AI decision with risk parameter validation"""
        try:
            # Check risk parameters before execution
            if not self._validate_risk_parameters(transaction_data):
                raise Exception("Transaction failed risk parameter validation")

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
    def _validate_risk_parameters(self, transaction_data):
        """Validate transaction against risk parameters"""
        from base_models import RiskParameter
        
        try:
            if not transaction_data:
                print("No transaction data provided")
                return False

            # Get active risk parameters
            risk_params = RiskParameter.query.filter_by(active=True).all()
            if not risk_params:
                print("No active risk parameters found")
                return False
                
            risk_param_dict = {param.parameter_type: param.value for param in risk_params}
            
            # Calculate transaction value in USD
            value_in_wei = transaction_data.get('value', 0)
            value_in_eth = self.w3.from_wei(value_in_wei, 'ether')
            
            # Get current AVAX price with retry mechanism
            avax_price = self._get_avax_price()
            if avax_price <= 0:
                print("Unable to get valid AVAX price")
                return False
                
            transaction_value_usd = value_in_eth * avax_price
            
            # Get wallet balance
            wallet = self.wallet_manager.get_wallet()
            if not wallet:
                print("No wallet configured")
                return False
                
            total_balance_wei = self.w3.eth.get_balance(wallet.address)
            total_balance_usd = self.w3.from_wei(total_balance_wei, 'ether') * avax_price
            
            # Check max exposure percentage
            max_exposure = risk_param_dict.get('max_exposure_percentage', 20.0)
            if total_balance_usd > 0:
                exposure_percentage = (transaction_value_usd / total_balance_usd) * 100
                if exposure_percentage > max_exposure:
                    print(f"Transaction exceeds max exposure percentage: {exposure_percentage:.2f}% > {max_exposure}%")
                    return False
            
            # Enhanced validation for swap/trade operations
            if transaction_data.get('type') in ['swap', 'trade']:
                # Validate slippage
                max_slippage = risk_param_dict.get('max_slippage', 1.0)
                estimated_slippage = transaction_data.get('estimated_slippage')
                if estimated_slippage is None:
                    print("Missing estimated slippage for swap/trade")
                    return False
                if estimated_slippage > max_slippage:
                    print(f"Estimated slippage exceeds maximum: {estimated_slippage:.2f}% > {max_slippage}%")
                    return False
                
                # Validate liquidity
                min_liquidity = risk_param_dict.get('min_liquidity', 100000)
                pool_liquidity = transaction_data.get('pool_liquidity')
                if pool_liquidity is None:
                    print("Missing pool liquidity information")
                    return False
                if pool_liquidity < min_liquidity:
                    print(f"Pool liquidity below minimum: ${pool_liquidity:,.2f} < ${min_liquidity:,.2f}")
                    return False
                
                # Validate profit threshold
                min_profit = risk_param_dict.get('min_profit_threshold', 0.5)
                estimated_profit = transaction_data.get('estimated_profit_percentage')
                if estimated_profit is None:
                    print("Missing estimated profit information")
                    return False
                if estimated_profit < min_profit:
                    print(f"Estimated profit below minimum threshold: {estimated_profit:.2f}% < {min_profit}%")
                    return False
            
            # Validate gas price multiplier
            max_gas_multiplier = risk_param_dict.get('max_gas_multiplier', 1.5)
            try:
                base_gas_price = self.w3.eth.gas_price
                transaction_gas_price = transaction_data.get('gasPrice', base_gas_price)
                if transaction_gas_price > (base_gas_price * max_gas_multiplier):
                    print(f"Gas price exceeds maximum multiplier: {max_gas_multiplier}x")
                    return False
            except Exception as e:
                print(f"Error validating gas price: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating risk parameters: {str(e)}")
            return False
            
    def _get_avax_price(self):
        """Get current AVAX price in USD"""
        try:
            import requests
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': 'avalanche-2', 'vs_currencies': 'usd'}
            )
            return float(response.json()['avalanche-2']['usd'])
        except Exception:
            return 0  # Return 0 to fail safe on price errors
