# Autonomous Avalanche AI Agent

An autonomous AI agent system for managing multi-chain Avalanche wallet transactions with secure key management and comprehensive risk controls. The platform integrates wallet management, chain scanning, and automated transaction execution capabilities through a web interface, supporting both Avalanche C-Chain and Fuji testnet operations.

## Features

- **Multi-chain Support**
  - Avalanche C-Chain and Fuji testnet compatibility
  - Chain-specific operation handling
  - Seamless chain switching
  - Real-time balance monitoring

- **Secure Wallet Management**
  - Encrypted key storage
  - Secure transaction signing
  - Multiple wallet support
  - Balance tracking across chains

- **Chain Scanning and Monitoring**
  - Real-time blockchain data analysis
  - Pattern recognition
  - Market data integration
  - Automated scanning cycles

- **Transaction Execution Engine**
  - Risk parameter validation
  - Slippage protection
  - Gas optimization
  - Transaction verification

- **Smart Contract Management**
  - Contract compilation
  - Automated deployment
  - Contract verification
  - ABI management

- **Advanced Memory System**
  - Pattern recognition
  - Transaction history analysis
  - Confidence scoring
  - Automated cleanup

- **Risk Parameter Management**
  - Configurable risk thresholds
  - Real-time validation
  - Parameter persistence
  - Default value management

## Architecture

### Core Components

1. **Wallet Manager** (`wallet_manager.py`)
   - Handles wallet creation and management
   - Manages encrypted private keys
   - Processes transactions
   - Manages chain switching

2. **Chain Scanner** (`chain_scanner.py`)
   - Monitors blockchain activity
   - Collects market data
   - Analyzes network conditions
   - Tracks gas prices

3. **Decision Engine** (`decision_engine.py`)
   - Processes chain data
   - Makes investment decisions
   - Integrates with memory system
   - Validates against risk parameters

4. **Transaction Executor** (`transaction_executor.py`)
   - Executes transactions
   - Validates risk parameters
   - Manages gas prices
   - Handles transaction confirmation

5. **Contract Manager** (`contract_manager.py`)
   - Manages smart contract deployment
   - Handles contract compilation
   - Verifies deployed contracts
   - Manages contract ABIs

6. **Memory Manager** (`memory_manager.py`)
   - Stores transaction patterns
   - Manages historical data
   - Implements pattern recognition
   - Handles data cleanup

### Database Models

```python
# Key models in base_models.py
Chain                # Chain configuration
WalletConfig        # Wallet information
Transaction         # Transaction records
Memory              # Pattern memory storage
AIDecision          # AI decision records
Contract            # Smart contract data
RiskParameter       # Risk control parameters
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/avalanche-ai-agent.git
cd avalanche-ai-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file with required variables
cp .env.example .env
```

4. Initialize the database:
```bash
python initialize_chains.py
python initialize_risk_params.py
```

5. Start the application:
```bash
python main.py
```

## Environment Variables

Required environment variables:

```
DATABASE_URL=postgresql://username:password@host:port/dbname
WALLET_ENCRYPTION_KEY=your-encryption-key
BRIANKNOWS_API_KEY=your-api-key
```

## Risk Parameters

The system includes several risk parameters that can be configured:

1. **Max Slippage** (default: 1.0%)
   - Maximum allowed slippage percentage for trades
   - Range: 0.1% - 5.0%

2. **Min Liquidity** (default: 100,000)
   - Minimum liquidity required in pool for trade execution
   - Range: 10,000 - 1,000,000

3. **Max Gas Multiplier** (default: 1.5x)
   - Maximum multiplier for gas price estimation
   - Range: 1.0x - 3.0x

4. **Min Profit Threshold** (default: 0.5%)
   - Minimum profit percentage required for trade execution
   - Range: 0.1% - 5.0%

5. **Max Exposure Percentage** (default: 20.0%)
   - Maximum percentage of portfolio to risk in a single trade
   - Range: 1.0% - 100.0%

## API Endpoints

### Wallet Management

```
GET /api/wallet/balance
GET /api/wallet/balance/<chain_id>
GET /api/wallet/chains
```

### Contract Management

```
POST /api/contracts/compile
POST /api/contracts/deploy
POST /api/contracts/verify
```

### Risk Parameters

```
GET /api/risk-parameters
PUT /api/risk-parameters/<param_id>
POST /api/risk-parameters/<param_id>/reset
```

### Transaction History

```
GET /api/transactions/recent
```

## Web Interface

The system provides a web interface with the following pages:

1. **Dashboard** (`/`)
   - Wallet balances
   - Recent activity
   - Performance metrics

2. **Transactions** (`/transactions`)
   - Transaction history
   - Status tracking
   - Chain filtering

3. **Contracts** (`/contracts`)
   - Contract deployment
   - Verification status
   - Contract management

4. **Risk Parameters** (`/risk-parameters`)
   - Parameter configuration
   - Value adjustment
   - Reset functionality

## Security Considerations

1. **Key Management**
   - Private keys are encrypted at rest
   - Encryption key stored in environment variables
   - Secure key generation process

2. **Risk Controls**
   - Multiple validation layers
   - Configurable risk parameters
   - Transaction verification

3. **Access Control**
   - API authentication
   - Secure session management
   - Environment variable protection

## Development

1. **Local Development**
```bash
# Start development server
python main.py
```

2. **Database Migrations**
```bash
# Initialize database
python initialize_chains.py
python initialize_risk_params.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
