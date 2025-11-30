"""
Backends personalizados para envío de emails.
"""
from .sendgrid_backend import SendGridBackend

__all__ = ['SendGridBackend']

