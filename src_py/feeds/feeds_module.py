from nest.core import Module
from .feeds_controller import FeedsController
from .feeds_service import FeedsService


@Module(
    controllers=[FeedsController],
    providers=[FeedsService],
    imports=[]
)   
class FeedsModule:
    pass

    