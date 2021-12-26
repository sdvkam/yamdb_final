import random
import string

from django.core.mail import send_mail

from api_yamdb.settings import DEFAULT_FROM_EMAIL


def get_confirmation_code():
    return ''.join(random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits,
        k=10))


def send_confirmation_code_email(email, confirmation_code):
    send_mail(
        'YaMBD confirmation code',
        f'Hello! Your confirmation code is {confirmation_code}.',
        DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False
    )
