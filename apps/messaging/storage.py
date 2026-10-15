from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateAudioStorage(FileSystemStorage):
    """Store voice messages outside MEDIA_ROOT so development URLs cannot expose them."""

    def __init__(self, location=None, base_url="/_private_audio_disabled/"):
        super().__init__(
            location=location or settings.PRIVATE_AUDIO_ROOT,
            base_url=base_url,
        )
