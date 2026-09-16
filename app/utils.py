import random
import string

from app.config import settings


def generate_short_code(length: int = settings.SHORT_CODE_LENGTH) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))
