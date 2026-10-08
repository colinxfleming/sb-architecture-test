"""Major data structures."""
from django.db import models
import logging
logger = logging.getLogger(__name__)

class Organization(models.Model):
    """Tenant model in multitenant environment."""
    name = models.TextField()

class MessagingClient(models.Model):
    """Sending config for interacting with providers such as Twilio."""
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    provider = models.TextField(choices=["Twilio", "Sinch"])
    sending_rate = models.IntegerField(help_text="How many messages we enqueue in a sending cycle")

class PhoneContact(models.Model):
    """"""
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    phone_number = models.TextField()

class PhoneList(models.Model):
    """A group of contacts for sending."""
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    phone_contacts = models.ArrayField(base_field=models.IntegerField(), help_text="A list of phone contact ids")

class Broadcast(models.Model):
    """Configuration for an individual broadcast to a group of contacts."""
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    messaging_client = models.ForeignKey(MessagingClient, on_delete=models.DO_NOTHING)
    send_status = models.TextField(choices=["draft", "processing", "sent"])

    phone_list = models.ForeignKey(PhoneList, on_delete=models.DO_NOTHING)
    text = models.TextField()
    image_url = models.TextField(null=True, blank=True, help_text="Optional URL of the text message image")

    def send(self) -> None:
        """Move a broadcast to sending. Triggered by clicking a button in the app."""
        if self.send_status != "draft":
            raise Exception("Broadcast already sending")
        self.send_status = "processing"
        self.save()

        # Create all messages
        messages_for_create = []
        for phone_contact in self.phone_list.phone_contacts:
            messages_for_create.append(
                PhoneMessage(phone_contact=phone_contact, broadcast=self, organization=self.organization)
            )
        PhoneMessage.objects.bulk_create(messages_for_create)
        logger.info(f"Began sending broadcast {self.id}")

class PhoneMessage(models.Model):
    """A text message."""
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    broadcast = models.ForeignKey(Broadcast, on_delete=models.DO_NOTHING)
    phone_contact = models.ForeignKey(PhoneContact)
    text = models.TextField(help_text="The rendered text content in the message")
    image_url = models.TextField(null=True, blank=True, help_text="Optional URL of the text message image")
    send_status = models.TextField(choices=["created", "sent_to_provider", "delivered"], default="created", help_text="Current status of a particular phone message")

    def send_message_to_provider(self):
        """Pretend this does the work to send a message to a texting provider service. Triggered by an async task."""
        logger.info(f"Sent message {self.id} to contact {self.phone_contact_id}")
