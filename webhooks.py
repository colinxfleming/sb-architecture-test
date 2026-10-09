"""Sent to us by a texting provider after we send them a message, to tell us how it went."""
import logging
from models import PhoneMessage
logger = logging.getLogger(__name__)

def receive_provider_status_update(payload: dict[str, str]) -> None:
    """Update a phonemessage send_status based on what happened according to the texting provider. Happens 1 to 60 seconds after sending most of the time."""
    message_id = payload.get('id')
    send_status = payload.get('status')
    message = PhoneMessage.objects.get(id=message_id)
    message.send_status = send_status
    message.save()
