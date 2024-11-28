from pathlib import Path
import json
import solcx
from web3 import Web3
from base_models import db, Chain
from datetime import datetime

class ContractManager:
    def __init__(self, wallet_manager):
        """Initialize contract manager with wallet manager"""
        self.wallet_manager = wallet_manager
        self.w3 = Web3(Web3.HTTPProvider(self.wallet_manager.chain.rpc_url))
        self._ensure_solc()
        
    def _ensure_solc(self):
        """Ensure Solidity compiler is installed"""
        try:
            solcx.install_solc(version='0.8.20')
            solcx.set_solc_version('0.8.20')
        except Exception as e:
            print(f"Error installing solc: {str(e)}")
            raise
            
    def compile_contract(self, source_code: str, contract_name: str):
        """Compile a Solidity contract"""
        try:
            compiled_sol = solcx.compile_source(
                source_code,
                output_values=['abi', 'bin'],
                solc_version='0.8.20'
            )
            contract_id = f'<stdin>:{contract_name}'
            return {
                'abi': compiled_sol[contract_id]['abi'],
                'bytecode': compiled_sol[contract_id]['bin']
            }
        except Exception as e:
            print(f"Error compiling contract: {str(e)}")
            raise
            
    def deploy_contract(self, compiled_contract: dict, constructor_args=None):
        """Deploy a compiled contract"""
        try:
            # Get wallet
            wallet = self.wallet_manager.get_wallet()
            if not wallet:
                raise Exception("No wallet configured")
                
            # Create contract deployment transaction
            contract = self.w3.eth.contract(
                abi=compiled_contract['abi'],
                bytecode=compiled_contract['bytecode']
            )
            
            # Prepare constructor arguments
            if constructor_args is None:
                constructor_args = []
                
            # Estimate gas for deployment
            deploy_txn = contract.constructor(*constructor_args).build_transaction({
                'from': wallet.address,
                'nonce': self.w3.eth.get_transaction_count(wallet.address),
                'gas': 2000000,  # Will be estimated
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Update gas estimate
            deploy_txn['gas'] = self.w3.eth.estimate_gas(deploy_txn)
            
            # Sign transaction
            signed_txn = self.wallet_manager.sign_transaction(deploy_txn)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'contract_address': tx_receipt['contractAddress'],
                'transaction_hash': tx_hash.hex(),
                'abi': compiled_contract['abi']
            }
            
        except Exception as e:
            print(f"Error deploying contract: {str(e)}")
            raise
            
    def verify_contract(self, contract_address: str, compiled_contract: dict):
        """Verify deployed contract code"""
        try:
            deployed_bytecode = self.w3.eth.get_code(Web3.to_checksum_address(contract_address))
            expected_bytecode = compiled_contract['bytecode']
            
            # Remove metadata hash from comparison (last 43 bytes)
            deployed_code = deployed_bytecode.hex()[:-86]
            expected_code = expected_bytecode[:-86]
            
            return deployed_code == expected_code
            
        except Exception as e:
            print(f"Error verifying contract: {str(e)}")
            return False
