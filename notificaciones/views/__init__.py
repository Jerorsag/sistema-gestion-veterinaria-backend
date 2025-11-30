from .test_email import TestEmailView

# Importar test_sendgrid_direct solo si existe (para evitar errores si no se subió)
try:
    from .test_sendgrid_direct import TestSendGridDirectView
    __all__ = ['TestEmailView', 'TestSendGridDirectView']
except ImportError:
    __all__ = ['TestEmailView']
