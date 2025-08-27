# Carbon Offset Estimator (FastAPI)

## Run Docker
- `docker build -t eco-footprint-api .`
- `docker run -p 8000:8000 -e OFFSET_RATE=0.02 eco-footprint-api`

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export WIDGET_DEFAULT_PLACEMENT="#cart_container"
export WIDGET_DEFAULT_VERBIAGE="Reduce my order's carbon footprint"
export OFFSET_RATE="0.02"
uvicorn app.main:app --reload