from flask import Flask, jsonify, request, render_template
from base_models import db, Chain, WalletConfig, Transaction, Memory, AIDecision, Contract, RiskParameter
from apscheduler.schedulers.background import BackgroundScheduler
import os

# Global components
wallet_manager = None
chain_scanner = None
decision_engine = None
transaction_executor = None
contract_manager = None

def init_app_components():
    """Initialize application components"""
    global wallet_manager, chain_scanner, decision_engine, transaction_executor, contract_manager
    
    try:
        from wallet_manager import WalletManager
        from chain_scanner import ChainScanner
        from decision_engine import DecisionEngine
        from transaction_executor import TransactionExecutor
        from contract_manager import ContractManager
        
        wallet_manager = WalletManager()
        chain_scanner = ChainScanner()
        decision_engine = DecisionEngine()
        transaction_executor = TransactionExecutor(wallet_manager)
        contract_manager = ContractManager(wallet_manager)
        return True
    except Exception as e:
        print(f"Error initializing components: {str(e)}")
        return False

def configure_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/transactions')
    def transactions():
        return render_template('transactions.html')

    @app.route('/contracts')
    def contracts_page():
        return render_template('contracts.html')

    @app.route('/risk-parameters')
    def risk_parameters():
        return render_template('risk_parameters.html')

    @app.route('/api/contracts/compile', methods=['POST'])
    def compile_contract():
        if not contract_manager:
            return jsonify({"error": "Contract manager not initialized"}), 500
        
        try:
            data = request.get_json()
            if not data or 'source_code' not in data or 'contract_name' not in data:
                return jsonify({"error": "Missing required fields"}), 400
                
            # Validate contract name
            if not data['contract_name'].isalnum():
                return jsonify({"error": "Contract name must be alphanumeric"}), 400
                
            # Validate source code
            if len(data['source_code'].strip()) < 10:
                return jsonify({"error": "Source code is too short"}), 400
                
            compiled = contract_manager.compile_contract(
                data['source_code'],
                data['contract_name']
            )
            
            # Save contract details in database
            contract = Contract(
                name=data['contract_name'],
                abi=compiled['abi'],
                bytecode=compiled['bytecode'],
                chain_id=wallet_manager.chain_id,
                verified=False,
                address='0x0000000000000000000000000000000000000000',  # Placeholder until deployed
                transaction_hash='0x0000000000000000000000000000000000000000000000000000000000000000'  # Placeholder
            )
            db.session.add(contract)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Contract compiled successfully",
                "data": compiled
            })
        except Exception as e:
            db.session.rollback()
            error_message = str(e)
            if "Error compiling" in error_message:
                return jsonify({"error": "Compilation error", "details": error_message}), 400
            return jsonify({"error": "Internal server error", "details": error_message}), 500

    @app.route('/api/contracts/deploy', methods=['POST'])
    def deploy_contract():
        if not contract_manager:
            return jsonify({"error": "Contract manager not initialized"}), 500
        
        try:
            data = request.get_json()
            if not data or 'compiled_contract' not in data:
                return jsonify({"error": "Missing required fields"}), 400
                
            constructor_args = data.get('constructor_args', [])
            deployment = contract_manager.deploy_contract(
                data['compiled_contract'],
                constructor_args
            )
            
            # Update contract in database
            contract = Contract.query.filter_by(
                chain_id=wallet_manager.chain_id,
                address='0x0000000000000000000000000000000000000000'
            ).first()
            
            if contract:
                contract.address = deployment['contract_address']
                contract.transaction_hash = deployment['transaction_hash']
                db.session.commit()
            
            return jsonify(deployment)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/contracts/verify', methods=['POST'])
    def verify_contract():
        if not contract_manager:
            return jsonify({"error": "Contract manager not initialized"}), 500
        
        try:
            data = request.get_json()
            if not data or 'contract_address' not in data or 'compiled_contract' not in data:
                return jsonify({"error": "Missing required fields"}), 400
                
            is_verified = contract_manager.verify_contract(
                data['contract_address'],
                data['compiled_contract']
            )
            
            if is_verified:
                # Update contract verification status
                contract = Contract.query.filter_by(
                    address=data['contract_address'],
                    chain_id=wallet_manager.chain_id
                ).first()
                
                if contract:
                    contract.verified = True
                    db.session.commit()
            
            return jsonify({"verified": is_verified})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/wallet/balance')
    @app.route('/api/wallet/balance/<int:chain_id>')
    def get_balance(chain_id=None):
        if not wallet_manager:
            return jsonify({"error": "Wallet manager not initialized"}), 500
        
        try:
            original_chain_id = wallet_manager.chain_id
            try:
                if chain_id is not None:
                    wallet_manager.switch_chain(chain_id)
                balance = wallet_manager.get_balance()
                current_chain = wallet_manager.chain
                return jsonify({
                    "balance": balance,
                    "chain_id": current_chain.id,
                    "symbol": current_chain.symbol,
                    "network_id": current_chain.network_id
                })
            finally:
                if chain_id is not None:
                    wallet_manager.switch_chain(original_chain_id)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/api/wallet/chains')
    def get_supported_chains():
        if not wallet_manager:
            return jsonify({"error": "Wallet manager not initialized"}), 500
        
        chains = wallet_manager.get_supported_chains()
        return jsonify(chains)

    @app.route('/api/transactions/recent')
    def get_recent_transactions():
        transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
        return jsonify([{
            'hash': tx.hash,
            'type': tx.type,
            'amount': tx.amount,
            'timestamp': tx.timestamp.isoformat(),
            'status': tx.status,
            'chain_id': tx.chain_id
        } for tx in transactions])

    @app.route('/api/risk-parameters', methods=['GET'])
    def get_risk_parameters():
        """Get all active risk parameters"""
        try:
            params = RiskParameter.query.filter_by(active=True).all()
            return jsonify([{
                'id': param.id,
                'parameter_type': param.parameter_type,
                'value': param.value,
                'min_value': param.min_value,
                'max_value': param.max_value,
                'default_value': param.default_value,
                'description': param.description
            } for param in params])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/risk-parameters/<int:param_id>', methods=['PUT'])
    def update_risk_parameter(param_id):
        """Update a risk parameter value"""
        try:
            data = request.get_json()
            if 'value' not in data:
                return jsonify({"error": "Missing value field"}), 400

            param = RiskParameter.query.get(param_id)
            if not param:
                return jsonify({"error": "Parameter not found"}), 404

            # Validate new value
            new_value = float(data['value'])
            if new_value < param.min_value or new_value > param.max_value:
                return jsonify({
                    "error": f"Value must be between {param.min_value} and {param.max_value}"
                }), 400

            param.value = new_value
            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"Updated {param.parameter_type} to {new_value}"
            })
        except ValueError:
            return jsonify({"error": "Invalid value format"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/risk-parameters/<int:param_id>/reset', methods=['POST'])
    def reset_risk_parameter(param_id):
        """Reset a risk parameter to its default value"""
        try:
            param = RiskParameter.query.get(param_id)
            if not param:
                return jsonify({"error": "Parameter not found"}), 404

            param.value = param.default_value
            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"Reset {param.parameter_type} to default value {param.default_value}"
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    def run_ai_cycle():
        """Execute one cycle of the AI agent's decision-making process across all chains"""
        with app.app_context():
            if not all([chain_scanner, decision_engine, transaction_executor]):
                print("Components not initialized")
                return

            try:
                # Get all active chains
                active_chains = Chain.query.filter_by(active=True).all()
                
                for chain in active_chains:
                    try:
                        # Switch to current chain
                        chain_scanner.switch_chain(chain.id)
                        transaction_executor.switch_chain(chain.id)
                        
                        # Scan chain data
                        chain_data = chain_scanner.scan_latest_data()
                        
                        # Get AI decision
                        decision = decision_engine.make_decision(chain_data)
                        
                        # Execute transaction if needed and passes risk validation
                        if decision.should_execute:
                            # Validate against risk parameters before execution
                            if transaction_executor._validate_risk_parameters(decision.transaction_data):
                                transaction_executor.execute_transaction(decision.transaction_data)
                            else:
                                print("Transaction rejected: Failed risk parameter validation")
                            
                    except Exception as chain_error:
                        print(f"Error processing chain {chain.name}: {str(chain_error)}")
                        continue
                    
            except Exception as e:
                print(f"Error in AI cycle: {str(e)}")

    # Initialize scheduler with app context
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_ai_cycle, 'interval', minutes=5)
    scheduler.start()

    return app

if __name__ == '__main__':
    from main import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
