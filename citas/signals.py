import django.dispatch

"""
Define las señales personalizadas (los "eventos" o "gritos")
que la app 'citas' enviará.
"""

# Define un proveedor de argumentos que enviará 'cita'
cita_signal_args = ["cita"]

cita_agendada_signal = django.dispatch.Signal(providing_args=cita_signal_args)
cita_cancelada_signal = django.dispatch.Signal(providing_args=cita_signal_args)
cita_reagendada_signal = django.dispatch.Signal(providing_args=cita_signal_args)