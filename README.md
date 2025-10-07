# FTSOv2 Example Value Provider

This is a sample implementation of an FTSOv2 value provider that serves values for requested feed IDs. By default, it uses [CCXT](https://ccxt.readthedocs.io/) to fetch the latest values from supported exchanges. Alternatively, it can be configured to provide fixed or random values for testing purposes.

## Configuration

The provider behavior can be adjusted via the `VALUE_PROVIDER_IMPL` environment variable:
- `ccxt`: (Default) uses the CCXT library to fetch real-time prices from various exchanges.
- `fixed`: returns a fixed value.
- `random`: returns random values.

## Starting the Provider

There are two ways to run the value provider:

### 1. Running with Python (Local Development)

**Prerequisites:**
- Python 3.8+
- Pip

**Installation:**

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/flare-foundation/ftso-v2-example-value-provider.git
cd ftso-v2-example-value-provider
pip install -r requirements.txt
```

**Running the server:**

```bash
python src/main.py
```

The server will start on `http://localhost:3101`.

### 2. Running with Docker

**Prerequisites:**
- Docker

**Build the Docker image:**

```bash
docker build -t ftso-v2-example-value-provider .
```

**Run the Docker container:**

```bash
docker run --rm -it -p 3101:3101 ftso-v2-example-value-provider
```

## API Documentation

Once the server is running, the OpenAPI specification (Swagger UI) is available at:

[http://localhost:3101/docs](http://localhost:3101/docs)

## Obtaining Feed Values

The provider exposes two API endpoints for retrieving feed values:

1. **`/feed-values/{voting_round_id}`**: Retrieves feed values for a specified voting round. Used by FTSO V2 Scaling clients.
2. **`/feed-values`**: Retrieves the latest feed values without a specific voting round ID. Used by FTSO V2 Fast Updates clients.

> **Note**: In this example implementation, both endpoints return the same data, which is the latest feed values available.

### Example Usage

#### Fetching Feed Values with a Voting Round ID

Use the endpoint `/feed-values/{voting_round_id}` to obtain values for a specific voting round.

```bash
curl -X 'POST' \
  'http://localhost:3101/feed-values/0' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "feeds": [
    { "category": 1, "name" : "BTC/USD" }
  ]
}'
```

**Example Response:**

```json
{
  "votingRoundId": 0,
  "data": [
    { "feed": { "category": 1, "name": "BTC/USD" }, "value": 71287.34508311428 }
  ]
}
```

#### Fetching Latest Feed Values (Without Voting Round ID)

Use the endpoint `/feed-values` to get the most recent feed values without specifying a voting round.

```bash
curl -X 'POST' \
  'http://localhost:3101/feed-values' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "feeds": [
    { "category": 1, "name" : "BTC/USD" }
  ]
}'
```

**Example Response:**

```json
{
  "data": [
    { "feed": { "category": 1, "name": "BTC/USD" }, "value": 71285.74004472858 }
  ]
}
```