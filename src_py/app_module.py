from nest.core import PyNestFactory, Module
from .config import config
from .app_controller import AppController
from .app_service import AppService
from src.feeds.feeds_module import FeedsModule


@Module(
    imports=[FeedsModule],
    controllers=[AppController],
    providers=[AppService],
)
class AppModule:
    pass


app = PyNestFactory.create(
    AppModule,
    description="This is my Async PyNest app.",
    title="PyNest Application",
    version="1.0.0",
    debug=True,
    # cors=True,
    # root_path="/",
)
http_server = app.get_server()


@http_server.on_event("startup")
async def startup():
    await config.create_all()
