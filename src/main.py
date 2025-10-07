import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from nest.core import PyNestFactory
from contextlib import asynccontextmanager

from app_module import AppModule
from data_feeds.ccxt_provider_service import CcxtFeed

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    """
    print("Starting up...")
    value_provider_impl = os.getenv("VALUE_PROVIDER_IMPL", "ccxt")
    if value_provider_impl == "ccxt":
        try:
            injector = app.extra['injector']
            ccxt_feed = injector.get(CcxtFeed)
            await ccxt_feed.start()
        except KeyError:
            print("Injector not found in app.extra. Could not start CcxtFeed.")
        except Exception as e:
            print(f"An error occurred during CcxtFeed startup: {e}")

    yield

    print("Shutting down...")


def main():
    app: FastAPI = PyNestFactory.create(
        AppModule,
        root_path="/",
        description="This server is used by the FTSO protocol data provider.",
        title="Simple Feed Value Provider API interface",
        version="1.0.0",
        cors=True,
    )

    # Set up lifespan events
    app.router.lifespan_context = lifespan

    port = int(os.getenv("VALUE_PROVIDER_CLIENT_PORT", 3101))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
