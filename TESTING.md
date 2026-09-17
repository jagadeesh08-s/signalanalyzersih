# SIH26147 Signal Analyzer - Testing Guide

## Running Tests

### Backend Tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
# or
npm run test:watch
```

## Test Coverage

The test suite covers:

- **test_classifier.py** - Modulation classification (HoC and ML)
- **test_signal_processing.py** - DSP functions (filtering, PSD, spectrogram, etc.)
- **test_demodulator.py** - Demodulation (BPSK, QPSK, FSK, etc.)
- **test_correlation.py** - Signal correlation analysis
- **test_pipeline.py** - Full analysis pipeline
- **test_reports.py** - Report generation (JSON, CSV, PDF)
- **test_api.py** - FastAPI endpoints

## Authentication

### Configuration

Set these environment variables:

```bash
# Backend (.env)
ENABLE_AUTH=true
API_KEY="your-secure-api-key-here"

# Frontend (.env.local)
NEXT_PUBLIC_API_KEY="your-secure-api-key-here"
```

### Usage

Include the API key in requests:

```bash
curl -H "X-API-Key: your-secure-api-key-here" http://localhost:8000/api/v1/stats
```

Or in JavaScript:

```javascript
fetch('/api/v1/stats', {
  headers: {
    'X-API-Key': 'your-secure-api-key-here'
  }
})
```

### Development Mode

By default, `ENABLE_AUTH=false` which allows all requests without authentication. Set `ENABLE_AUTH=true` in production.

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - Database connection string
- `API_KEY` - API key for authentication
- `ENABLE_AUTH` - Enable/disable authentication
- `NEXT_PUBLIC_API_URL` - Backend API URL (frontend)
- `NEXT_PUBLIC_API_KEY` - API key for frontend requests

## CI/CD

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Backend Tests
  run: |
    cd backend
    pip install -r requirements.txt
    python -m pytest tests/ --cov=app --cov-report=xml

- name: Run Frontend Tests
  run: |
    cd frontend
    npm ci
    npm test
```