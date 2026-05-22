# Testing strategy

The suite is split by risk and runtime cost:

- `unit`: no database and no network. Use this for pure service logic, SQL generation, security helpers, and payload normalization helpers.
- `integration`: uses the local MySQL test database and FastAPI `TestClient`. DHL is mocked with a realistic payload captured from the mock API.
- `contract`: calls the Railway DHL mock API directly and validates its response shape for the known tracking IDs.
- `e2e`: reserved for full flows that combine the API, database, and external mock API.
- `external`: any test that performs network calls. These tests are skipped unless `--run-external` is passed.

## Local commands

Run fast tests that do not need MySQL:

```bash
python -m pytest -m unit
```

Run the API integration suite:

```bash
docker compose up -d mysql
python -m pytest -m integration
```

Run the DHL mock contract tests:

```bash
python -m pytest -m contract --run-external
```

Run everything except external network tests:

```bash
python -m pytest
```

## DHL mock API

The contract tests call:

```text
https://shipment-tracker-mock-api-production.up.railway.app/track/shipments
```

The mock validates that `DHL-API-Key` is 32 alphanumeric characters. For local tests, this value is enough:

```text
1234567890ABCDEF1234567890ABCDEF
```

The 20 known tracking IDs are covered in `tests/contracts/test_dhl_mock_contract.py`.
