import requests
from datetime import datetime
from models import AIDecision, db

class DecisionEngine:
    def __init__(self):
        self.brianknows_api_key = "YOUR_BRIANKNOWS_API_KEY"
        self.api_url = "https://api.brianknows.ai/v1/decide"
        
    def make_decision(self, chain_data):
        """Make investment decision based on chain data"""
        decision_request = self._prepare_decision_request(chain_data)
        
        try:
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
            
            return Decision(
                should_execute=decision_data['should_execute'],
                transaction_data=decision_data['transaction_data']
            )
            
        except Exception as e:
            print(f"Error making decision: {str(e)}")
            return Decision(should_execute=False, transaction_data=None)
            
    def _prepare_decision_request(self, chain_data):
        """Prepare the decision request for the AI API"""
        return {
            "context": {
                "timestamp": datetime.utcnow().isoformat(),
                "chain": "avalanche",
                "block_number": chain_data['block_number'],
                "market_data": {
                    "price": chain_data['market_data']['avalanche-2']['usd'],
                    "yields": chain_data['yields']
                }
            },
            "parameters": {
                "risk_tolerance": "medium",
                "min_yield": 5.0,
                "max_gas_price": chain_data['gas_price'] * 1.5
            }
        }

class Decision:
    def __init__(self, should_execute, transaction_data):
        self.should_execute = should_execute
        self.transaction_data = transaction_data
