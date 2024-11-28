import requests
from datetime import datetime
from base_models import AIDecision, db
from memory_manager import MemoryManager

class DecisionEngine:
    def __init__(self):
        self.brianknows_api_key = "YOUR_BRIANKNOWS_API_KEY"
        self.api_url = "https://api.brianknows.ai/v1/decide"
        self.memory_manager = MemoryManager()
        
    def make_decision(self, chain_data):
        """Make investment decision based on chain data and past memories"""
        try:
            # Get relevant transaction patterns
            patterns = self.memory_manager.retrieve_memory('transaction_pattern')
            preferences = self.memory_manager.retrieve_memory('user_preference')
            
            # Enhance decision request with historical data
            decision_request = self._prepare_decision_request(chain_data, patterns, preferences)
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.brianknows_api_key}",
                    "Content-Type": "application/json"
                },
                json=decision_request
            )
            
            decision_data = response.json()
            
            # Create AI decision record
            decision = AIDecision(
                decision_type=decision_data['type'],
                confidence=decision_data['confidence'],
                reasoning=decision_data['reasoning']
            )
            db.session.add(decision)
            db.session.commit()
            
            # Store the decision pattern if it's a new type
            if decision_data['should_execute']:
                pattern_key = f"{decision_data['type']}_{datetime.utcnow().strftime('%Y%m')}"
                self.memory_manager.store_transaction_pattern(
                    pattern_key,
                    {
                        'type': decision_data['type'],
                        'conditions': chain_data,
                        'outcome': decision_data['transaction_data']
                    }
                )
            
            return Decision(
                should_execute=decision_data['should_execute'],
                transaction_data=decision_data['transaction_data']
            )
            
        except Exception as e:
            print(f"Error making decision: {str(e)}")
            return Decision(should_execute=False, transaction_data=None)
            
    def _prepare_decision_request(self, chain_data, patterns=None, preferences=None):
        """Prepare the decision request with historical context"""
        from base_models import RiskParameter
        
        # Get current risk parameters
        risk_params = {}
        try:
            active_params = RiskParameter.query.filter_by(active=True).all()
            for param in active_params:
                risk_params[param.parameter_type] = param.value
        except Exception as e:
            print(f"Error fetching risk parameters: {str(e)}")
            # Use defaults if DB query fails
            risk_params = {
                'max_slippage': 1.0,
                'min_liquidity': 100000,
                'max_gas_multiplier': 1.5,
                'min_profit_threshold': 0.5,
                'max_exposure_percentage': 20.0
            }
        
        # Calculate success patterns
        successful_patterns = []
        if patterns:
            successful_patterns = [p['value'] for p in patterns if p['confidence'] > 0.7]
        
        return {
            "context": {
                "timestamp": datetime.utcnow().isoformat(),
                "chain": "avalanche",
                "block_number": chain_data['block_number'],
                "market_data": {
                    "price": chain_data['market_data']['avalanche-2']['usd'],
                    "yields": chain_data['yields']
                },
                "historical_patterns": successful_patterns,
                "liquidity_data": chain_data.get('liquidity_data', {})
            },
            "parameters": {
                "max_slippage": risk_params.get('max_slippage', 1.0),
                "min_liquidity": risk_params.get('min_liquidity', 100000),
                "max_gas_multiplier": risk_params.get('max_gas_multiplier', 1.5),
                "min_profit_threshold": risk_params.get('min_profit_threshold', 0.5),
                "max_exposure_percentage": risk_params.get('max_exposure_percentage', 20.0),
                "current_gas_price": chain_data['gas_price']
            }
        }

class Decision:
    def __init__(self, should_execute, transaction_data):
        self.should_execute = should_execute
        self.transaction_data = transaction_data
