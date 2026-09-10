from django.conf import settings


def store_context():
    return {
        "store_name": settings.STORE_NAME,
        "store_document": settings.STORE_DOCUMENT,
        "store_address": settings.STORE_ADDRESS,
        "store_phone": settings.STORE_PHONE,
        "store_footer": settings.STORE_FOOTER,
    }
