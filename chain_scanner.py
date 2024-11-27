from web3 import Web3
import json
import requests

class ChainScanner:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
        self.yield_contracts = {
            'aave': '0x4F01AeD16D97E3aB5ab2B501154DC9bb0F1A5A2C',
            'benqi': '0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4',
        }
        
    def scan_latest_data(self):
        """Scan latest blockchain data for yield opportunities"""
        data = {
            'block_number': self.w3.eth.block_number,
            'yields': self._get_yield_data(),
            'gas_price': self.w3.eth.gas_price,
            'market_data': self._get_market_data()
        }
        return data
        
    def _get_yield_data(self):
        """Get current yield rates from various protocols"""
        yields = {}
        
        for protocol, contract in self.yield_contracts.items():
            try:
                # This is a simplified example - actual implementation would need
                # protocol-specific ABI and logic
                contract = self.w3.eth.contract(
                    address=contract,
                    abi=self._get_protocol_abi(protocol)
                )
                yields[protocol] = contract.functions.getYield().call()
            except Exception as e:
                print(f"Error getting yield for {protocol}: {str(e)}")
                yields[protocol] = 0
                
        return yields
        
    def _get_market_data(self):
        """Get current market data from external API"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': 'avalanche-2',
                    'vs_currencies': 'usd'
                }
            )
            return response.json()
        except Exception as e:
            print(f"Error getting market data: {str(e)}")
            return {'avalanche-2': {'usd': 0}}
            
    def _get_protocol_abi(self, protocol):
        """Load protocol-specific ABI"""
        # In production, these would be loaded from files
        return [
            {
                "inputs": [],
                "name": "getYield",
                "outputs": [{"type": "uint256", "name": ""}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
