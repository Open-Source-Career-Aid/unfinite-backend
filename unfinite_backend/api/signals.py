from django.dispatch import Signal, receiver
from .models import EventLog

log_signal = Signal()

@receiver(log_signal)
def log_event(sender, **kwargs):

    # possible kwargs:
    # user_id = kwargs.get('user_id')
    # query_id = kwargs.get('query_id')
    # query_was_new = kwargs.get('query_was_new')
    # serp_id = kwargs.get('serp_id')
    # search_was_new = kwargs.get('search_was_new')
    # completion_id = kwargs.get('completion_id')
    # completion_idx = kwargs.get('completion_idx')
    # desc = kwargs.get('desc')

    e = EventLog.objects.create(**{k: v for k,v in kwargs.items() if k != 'signal'})
    e.save()