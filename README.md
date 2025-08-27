# Shopify Web App
This app is a proof of concept for a development of a widget for Shopify, the backend is based on Python/FastAPI and Remix/React/TypeScript for the frontend.

## Pre requisites

- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **Shopify CLI** installed globally: `npm install -g @shopify/cli @shopify/theme`
- **Docker** (optional, for containerized backend)
- **Shopify Partner Account** and development store

## Shopify App Frontend
`/eco-footprint`: Scaffolded with the Shopify App Template

### Start Development Server
```bash
# in app root
shopify app dev
```

### Deploy
```bash
shopify app deploy
shopify app release
```

## Backend API
`/eco-footprint-api`: FastAPI backend for carbon offset calculations and widget configuration

## Run backend with Docker
```bash
docker build -t eco-footprint-api .
docker run -p 8000:8000 -e OFFSET_RATE=0.02 eco-footprint-api
```

## Run backend locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OFFSET_RATE="0.02"
uvicorn app.main:app --reload
```

### Environment Variables

The following environment variables can be configured:
- `OFFSET_RATE`: Carbon offset rate as decimal (default: 0.02 = 2%)

### Endpoints

- **GET** `/v1/config?shop={shop}` → `{ placement, verbiage }`
- **POST** `/v1/estimate` → `{ subtotal_cents, estimate_cents, rate, currency }`
- **POST** `/v1/opt-in` → persists record for monthly invoice aggregation
- **GET** `/v1/invoices/preview?shop={shop}&month=YYYY-MM`

### Notes / Assumptions

- **Estimator**: Uses placeholder formula `offset = subtotal * 0.02` per spec
- **Opt-ins**: Keyed by `cart_token + YYYY-MM` to avoid double-charges and support monthly rollups
- **Cart attributes**: `carbon_offset_opt_in`, `carbon_offset_cents` allow checkout surfaces to read the choice
- **Multi-merchant ready**: Config keyed by shop domain; future: use HMAC verification / API keys