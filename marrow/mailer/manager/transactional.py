# encoding: utf-8

"""Currently unsupported and non-functional."""

raise ImportError("This module is currently unsupported.")


import transaction

from functools import partial

from zope.interface import implements
from transaction.interfaces import IDataManager
  
from marrow.mailer.manager.dynamic import ScalingPoolExecutor, DynamicManager


__all__ = ['TransactionalDynamicManager']

log = __import__('logging').getLogger(__name__)



class ExecutorDataManager(object):
    implements(IDataManager)
    
    __slots__ = ('callback', 'abort_callback')
    
    def __init__(self, callback, abort=None, pool=None):
        self.callback = callback
        self.abort_callback = abort
    
    def commit(self, transaction):
        pass
    
    def abort(self, transaction):
        if self.abort_callback:
            self.abort_callback()
    
    def sortKey(self):
        return id(self)
    
    def abort_sub(self, transaction):
        pass
    
    commit_sub = abort_sub
    
    def beforeCompletion(self, transaction):
        pass
    
    afterCompletion = beforeCompletion
    
    def tpc_begin(self, transaction, subtransaction=False):
        if subtransaction:
            raise RuntimeError()
    
    def tpc_vote(self, transaction):
        pass
    
    def tpc_finish(self, transaction):
        self.callback()
    
    tpc_abort = abort


class TransactionalScalingPoolExecutor(ScalingPoolExecutor):
    def _submit(self, w):
        self._work_queue.put(w)
        self._adjust_thread_count()
    
    def _cancel_tn(self, f):
        if f.cancel():
            f.set_running_or_notify_cancel()
    
    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            
            f = _base.Future()
            w = _WorkItem(f, fn, args, kwargs)
            
            dm = ExecutorDataManager(partial(self._submit, w), partial(self._cancel_tn, f))
            transaction.get().join(dm)
            
            return f


class TransactionalDynamicManager(DynamicManager):
    name = "Transactional dynamic"
    Executor = TransactionalScalingPoolExecutor
