from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .consumers import PharmacyStatusConsumer


def push_pharmacy_status(data: dict) -> None:
    """Fan out a pharmacy/prescription status change to all connected boards."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        PharmacyStatusConsumer.GROUP, {"type": "status.update", "data": data}
    )
