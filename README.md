# FTSOv2 Example Feed Value Provider

This is a sample implementation of an FTSOv2 feed value provider that serves values for requested feed IDs.

## Architecture Overview

The application is built using the [NestJS](https.nestjs.com) framework and is structured as follows:

- **`main.ts`**: The entry point of the application. It bootstraps the NestJS application, sets up Swagger for API documentation, and starts the server.
- **`app.module.ts`**: The root module of the application. It uses a factory to dynamically select and instantiate the data provider based on the `VALUE_PROVIDER_IMPL` environment variable.
- **`app.controller.ts`**: The controller that exposes the API endpoints for retrieving feed values and volumes.
- **`app.service.ts`**: The service that contains the core business logic. It retrieves data from the selected data provider and returns it to the controller.
- **Data Providers**: The application includes three data providers:
    - `CcxtFeed`: Fetches real-time data from cryptocurrency exchanges using the [CCXT](https://ccxt.readthedocs.io/) library.
    - `FixedFeed`: Returns a fixed, hardcoded value for testing purposes.
    - `RandomFeed`: Returns random values for testing purposes.

## Data Providers

The application can be configured to use one of the following data providers, depending on the value of the `VALUE_PROVIDER_IMPL` environment variable:

- **`ccxt` (default)**: Uses the `CcxtFeed` to fetch real-time data from various cryptocurrency exchanges. This is the default provider if `VALUE_PROVIDER_IMPL` is not set.
- **`fixed`**: Uses the `FixedFeed` to return a hardcoded value. This is useful for testing scenarios where a predictable value is required.
- **`random`**: Uses the `RandomFeed` to return a random value. This is useful for testing scenarios where a dynamic but not necessarily real-world value is needed.

## Configuration

The application can be configured using the following environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `VALUE_PROVIDER_IMPL` | The data provider to use. Can be `ccxt`, `fixed`, or `random`. | `ccxt` |
| `VALUE_PROVIDER_CLIENT_PORT` | The port on which the server will listen. | `3101` |
| `VALUE_PROVIDER_CLIENT_BASE_PATH` | The base path for the API endpoints. | `` |
| `LOG_LEVEL` | The log level. Can be `log`, `debug`, or `warn`. | `log` |
| `RANDOM_FEED_UPDATE_INTERVAL` | The interval (in milliseconds) at which the random feed generates new values. | `1000` |
| `FIXED_FEED_VALUE` | The fixed value to be returned by the fixed feed. | `12345.6789` |

## Starting the Provider

To start the provider using Docker, run:

```bash
docker run --rm -it --publish "0.0.0.0:3101:3101" ghcr.io/flare-foundation/ftso-v2-example-value-provider
```

This will start the service on port `3101`. You can find the API spec at: http://localhost:3101/api-doc.

## API Endpoints

The provider exposes the following API endpoints:

### `/feed-values/:votingRoundId`

Retrieves feed values for a specified voting round. This endpoint is primarily used by FTSOv2 Scaling clients.

- **Method**: `POST`
- **Parameters**:
    - `votingRoundId` (path): The ID of the voting round.
- **Request Body**: `FeedValuesRequest`
    ```json
    {
      "feeds": [
        { "category": 1, "name": "BTC/USD" }
      ]
    }
    ```
- **Example Response**: `RoundFeedValuesResponse`
    ```json
    {
      "votingRoundId": 0,
      "data": [
        { "feed": { "category": 1, "name": "BTC/USD" }, "value": 71287.34508311428 }
      ]
    }
    ```

### `/feed-values/`

Retrieves the latest feed values without a specific voting round ID. This endpoint is primarily used by FTSOv2 Fast Updates clients.

- **Method**: `POST`
- **Request Body**: `FeedValuesRequest`
- **Example Response**: `FeedValuesResponse`
    ```json
    {
      "data": [
        { "feed": { "category": 1, "name": "BTC/USD" }, "value": 71285.74004472858 }
      ]
    }
    ```

### `/volumes/`

Retrieves the trading volumes for the requested feeds over a specified time window.

- **Method**: `POST`
- **Query Parameters**:
    - `window` (optional): The time window in seconds for which to retrieve the volume. Defaults to `60`.
- **Request Body**: `FeedValuesRequest`
- **Example Response**: `FeedVolumesResponse`
    ```json
    {
      "data": [
        { "feed": { "category": 1, "name": "BTC/USD" }, "volume": 12345.6789 }
      ]
    }
    ```

## Local Development

To run the application locally for development, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/flare-foundation/ftso-v2-example-value-provider.git
    cd ftso-v2-example-value-provider
    ```
2.  **Install dependencies**:
    ```bash
    yarn install
    ```
3.  **Run the application**:
    ```bash
    yarn start:dev
    ```

The application will be available at `http://localhost:3101`. Any changes you make to the source code will be automatically reloaded.

### Running in a container
Follow these steps:
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/flare-foundation/ftso-v2-example-value-provider.git
    cd ftso-v2-example-value-provider
    ```
2.  **Build the image**
    ```bash
    docker build -t ftso-v2-example-value-provider .
    ```
3.  **Run the container**
    ```bash
    docker run --rm -it -p 3101:3101 ftso-v2-example-value-provider
    ```
The application will be available at `http://localhost:3101`.
You can use environment variables to configure the application. For example, to use the `random` provider, run:
    ```bash
    docker run --rm -it -p 3101:3101 -e VALUE_PROVIDER_IMPL=random ftso-v2-example-value-provider
    ```