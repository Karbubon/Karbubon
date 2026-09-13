# Arbitrage Scanner — Crypto Arbitrage Detection System

![MIT](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-4169E1?logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?logo=tailwindcss)

A professional, real-time cryptocurrency arbitrage scanner that identifies profitable price differences across multiple exchanges. Built with Python, FastAPI, Next.js, and PostgreSQL.

## 🚀 Features

- **Multi-Exchange Support**: MEXC, Bitget, KuCoin, Bybit (extensible to any CCXT-supported exchange)
- **Real-time Scanning**: REST API with WebSocket for instant arbitrage alerts
- **Smart Volume Matching**: Uses order book depth to calculate real executable volumes, not just top prices
- **Fee Calculation**: Accounts for exchange trading fees and network transfer fees
- **CoinMarketCap Integration**: Displays coin rankings, market cap, and price data
- **User Dashboard**: Filter by profit %, volume, commission, symbols, blacklist/whitelist
- **History & Analytics**: Track all detected opportunities with pagination and filtering
- **Modern UI**: Responsive Next.js frontend with Tailwind CSS

## 🖼 Screenshots

![History Page](public/history.png)

![Settings Page](public/settings.png)

## 🏗 Architecture
```text
┌─────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Dashboard│  │ Settings │  │ History  │  │ Charts/Logs  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
│       │             │             │               │         │
│       └─────────────┴─────────────┴───────────────┘         │
│                              │ REST + WebSocket             │
└──────────────────────────────┼──────────────────────────────┘
                               │
┌──────────────────────────────┼────────────────────────────────┐
│                              ▼                                │
│                        FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │       WebSocket Manager (broadcast to connected clients) │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  /api/opps   │  │  /api/stats  │  │  /api/cmc          │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└──────────────────────────────┼────────────────────────────────┘
                               │
┌──────────────────────────────┼────────────────────────────────┐
│                              ▼                                │
│                   Arbitrage Engine (asyncio)                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         Parallel Order Book Fetcher (REST polling)     │   │
│  └────────────┬─────────────┬─────────────┬───────────────┘   │
│            ┌──▼────┐    ┌───▼────┐    ┌───▼────┐              │
│            │ MEXC  │    │ KuCoin │    │ Bybit  │    ...       │
│            └──┬────┘    └───┬────┘    └───┬────┘              │
│               └─────────────┴─────────────┘                   │
│                             │                                 │
│  ┌──────────────────────────┴──────────────────────────────┐  │
│  │              Spread Analyzer + Volume Matcher           │  │
│  │             - Order book depth analysis                 │  │
│  │             - Fee calculation (exchange + network)      │  │
│  │             - Network compatibility check               │  │
│  └───────────────────────────┬─────────────────────────────┘  │
└──────────────────────────────┼────────────────────────────────┘
                               │
                        ┌──────┴──────┐
                        │             │
                        ▼             ▼
               ┌──────────────────┐ ┌──────────────────┐
               │    PostgreSQL    │ │  CoinMarketCap   │
               │  (persistence)   │ │  API (top data)  │
               └──────────────────┘ └──────────────────┘
```


## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend API** | FastAPI (Python) |
| **Scanner Engine** | Python asyncio + CCXT |
| **Database** | PostgreSQL + SQLAlchemy ORM |
| **Frontend** | Next.js 16 (App Router) + Tailwind CSS |
| **Real-time** | WebSocket |
| **HTTP Client** | Axios |
| **Icons** | Lucide React |

## 📊 How It Works

### 1. Market Data Collection
- Scans all USDT spot pairs across configured exchanges
- Fetches order books with configurable depth (20-50 levels)
- Parallel REST polling with rate limiting

### 2. Candidate Detection
- Identifies pairs with positive spread across exchanges
- Filters by user-defined parameters (profit %, volume, commission)
- Checks network compatibility for transfers

### 3. Volume Matching
- Uses **weighted average prices** from order book depth
- Calculates real executable volume = min(buy_volume, sell_volume)
- Accounts for slippage and liquidity constraints

### 4. Profit Calculation
- Gross profit = (sell_price - buy_price) × volume
- Net profit = gross - exchange_fees - transfer_fees
- Shows real profit after all costs

### 5. Storage & Display
- Saves opportunities to PostgreSQL
- Real-time WebSocket updates
- REST API for history and statistics

## 📁 Project Structure
```text
arbitrage-scanner/
├── backend/
│ ├── api/ # FastAPI endpoints
│ │ ├── opportunities.py # Arbitrage CRUD
│ │ ├── stats.py # Statistics endpoints
│ │ ├── settings.py # User settings
│ │ ├── websocket.py # WebSocket manager
│ │ └── cmc.py # CoinMarketCap proxy
│ ├── models.py # SQLAlchemy models
│ ├── schemas.py # Pydantic schemas
│ ├── database.py # DB connection
│ ├── config.py # Configuration
│ └── main.py # FastAPI app
├── engine/
│ ├── scanner_v2.py # Main arbitrage scanner
│ └── archive/ # Legacy versions
├── frontend/
│ ├── app/
│ │ ├── page.tsx # Dashboard
│ │ ├── history/ # History page
│ │ └── settings/ # Settings page
│ ├── components/ # React components
│ │ ├── OpportunityCard.tsx
│ │ └── Header.tsx
│ ├── hooks/ # Custom hooks
│ │ └── useWebSocket.ts
│ ├── lib/ # API client
│ │ └── api.ts
│ └── types/ # TypeScript types
├── scripts/
│ ├── init_db_v2.py # DB initialization
│ ├── update_cmc_data.py # CMC data updater
│ └── update_schema.py # Schema migrations
├── run_api.py # API starter
└── requirements.txt
```

## 🔧 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Clone Repository
```bash
git clone https://github.com/slyfrs/arbitrage-scanner.git
cd arbitrage-scanner
```
### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and CMC API key
```
### 3. Database Setup
```bash
# Create PostgreSQL database
createdb arbitrage_scanner

# Initialize tables
python scripts/init_db_v2.py

# Update CMC data (requires API key)
python scripts/update_cmc_data.py
```
### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
## 🚀 Running the System
### Terminal 1: Scanner Engine
```bash
python engine/scanner_v2.py
```
### Terminal 2: API Server
```bash
python run_api.py
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```
### Terminal 3: Frontend
```bash
cd frontend
npm run dev
# Frontend available at http://localhost:3000
```
## 📡 API Endpoints
```table
Method	Endpoint	Description
GET	/api/opportunities/active	Active arbitrage opportunities
GET	/api/opportunities/history	Paginated history
GET	/api/opportunities/{id}	Single opportunity details
GET	/api/stats/overview	Dashboard statistics
GET	/api/stats/daily	Daily profit stats
GET	/api/settings	User settings
POST	/api/settings/{key}	Update setting
GET	/api/cmc/{symbol}	CoinMarketCap data
WS	/api/ws/opportunities	Real-time updates
```
## ⚙️ Configuration
Edit .env file:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/arbitrage_scanner

# Scanner Settings
MAX_VOLUME_USD=2000          # Max trade size
MIN_PROFIT_PERCENT=0.05      # Min profit % to show
SCAN_INTERVAL=15             # Seconds between scans
ORDERBOOK_DEPTH=20           # Order book depth

# CoinMarketCap
CMC_API_KEY=your_api_key
```

## 🎯 Dashboard Features
- Real-time cards with buy/sell prices, volumes, fees

- Filter by: min profit %, volume range, max commission

- Symbol filters: whitelist/blacklist specific coins

- Quick actions: add to blacklist/whitelist from card

- CMC data: coin rank, market cap, 24h change

- WebSocket live updates with sound notifications

## 📈 Example Output
```text
======================================================================
💰 [АРБИТРАЖ #1] SOL/USDT
======================================================================
SOL: MEXC→KuCoin +$2.45 (0.122%)

📗 ПОКУПКА: MEXC
   Цена: 65.13000000 [65.13000000 - 65.13000000]
   Объем: $2000.00 | 30.7078 монет | 1 ордеров

📕 ПРОДАЖА: KuCoin
   Цена: 65.20964185 [65.20000000 - 65.21000000]
   Объем: $2002.45 | 30.7078 монет | 2 ордеров

💰 ПРИБЫЛЬ: +$2.45 (0.122%)
```

## 🔍 Troubleshooting
### WebSocket connection fails
- Ensure API is running on port 8000

- Check CORS settings in backend/main.py

- Verify WebSocket URL: ws://localhost:8000/api/ws/opportunities
## No arbitrage opportunities found
- Run scanner in separate terminal

- Check exchange API connectivity

- Reduce MIN_PROFIT_PERCENT in settings
## CMC API rate limits (429 errors)
- Free tier: 333 requests/day

- Data is cached in database, updated on scanner start

- Run python scripts/update_cmc_data.py manually

## 📄 License

[MIT](LICENSE)

## 🤝 Contributing
1. Fork the repository

2. Create feature branch (git checkout -b feature/amazing)

3. Commit changes (git commit -m 'Add amazing feature')

4. Push to branch (git push origin feature/amazing)

5. Open Pull Request

## ⚠️ Disclaimer
```text
This tool is for educational purposes only. Cryptocurrency trading carries significant risk. Always verify calculations and never trade more than you can afford to lose. The authors are not responsible for any financial losses incurred through use of this software.
```
## 🌟 Acknowledgments
- CCXT - Unified cryptocurrency API

- FastAPI - Modern web framework

- Next.js - React framework

- CoinMarketCap - Market data

### Built with ❤️ for crypto arbitrage traders