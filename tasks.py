"""Asynchronous tasks executed from a queue."""
from celery import shared_task
import random
import logging
from models import Broadcast, MessagingClient, PhoneMessage
logger = logging.getLogger(__name__)

@shared_task
def send_phone_messages_all_orgs() -> None:
    """Start the process for an org to send a batch of phone messages to a provider. This task is queued once a minute on a schedule."""
    logger.info(f"Starting a message sending cycle")
    processing_orgs = set(Broadcast.objects.filter(send_status="processing").values_list("organization_id", flat=True))
    for organization_id in processing_orgs:
        logger.info(f"Triggering a message sending cycle in {organization_id}")
        send_phone_messages_for_org.delay(organization_id)

@shared_task
def send_phone_messages_for_org(organization_id: int) -> None:
    """Send messages to provider. Triggered by send_phone_messages_all_orgs."""
    logger.info(f"Starting a message sending cycle for {organization_id}")
    processing_broadcasts = Broadcast.objects.filter(organization_id=organization_id, send_status='processing')
    messaging_client = MessagingClient.objects.get(organization_id=organization_id)

    # Pull a batch of messages for sending
    eligible_messages_for_send = PhoneMessage.objects.filter(send_status="created", broadcast__in=[processing_broadcasts])
    random.shuffle(eligible_messages_for_send)
    eligible_messages_for_send = eligible_messages_for_send[:messaging_client.sending_rate]

    # Set the content of the message from the broadcast and ship it to the provider.
    logger.info(f"Sending {len(eligible_messages_for_send)} messages in {organization_id}")
    for message in eligible_messages_for_send:
        message.text = message.broadcast.text
        message.image_url = message.broadcast.image_url
        message.send_message_to_provider()
        message.send_status = 'sent_to_provider'
        message.save()
    logger.info(f"Completed sending cycle for {organization_id}")
