"""

  peasoup.util:  misc utility functions for peasoup

"""
import sys
import os

#  Since Peaoup will have
#  every invocation, we want as little overhead as possible when importing
#  the main module.  We therefore use a simple lazy-loading scheme for many
#  of our imports, built from the functions below.

def lazy_import(func):
    """Decorator for declaring a lazy import.

    This decorator turns a function into an object that will act as a lazy
    importer.  Whenever the object's attributes are accessed, the function
    is called and its return value used in place of the object.  So you
    can declare lazy imports like this:

        @lazy_import
        def socket():
            import socket
            return socket

    The name "socket" will then be bound to a transparent object proxy which
    will import the socket module upon first use.

    The syntax here is slightly more verbose than other lazy import recipes,
    but it's designed not to hide the actual "import" statements from tools
    like py2exe or grep.
    """
    try:
        f = sys._getframe(1)
    except Exception:
        namespace = None
    else:
        namespace = f.f_locals
    return _LazyImport(func.__name__,func,namespace)


class _LazyImport(object):
    """Class representing a lazy import."""

    def __init__(self,name,loader,namespace=None):
        self._esky_lazy_target = _LazyImport
        self._esky_lazy_name = name
        self._esky_lazy_loader = loader
        self._esky_lazy_namespace = namespace

    def _esky_lazy_load(self):
        if self._esky_lazy_target is _LazyImport:
            self._esky_lazy_target = self._esky_lazy_loader()
            ns = self._esky_lazy_namespace
            if ns is not None:
                try:
                    if ns[self._esky_lazy_name] is self:
                        ns[self._esky_lazy_name] = self._esky_lazy_target
                except KeyError:
                    pass

    def __getattribute__(self,attr):
        try:
            return object.__getattribute__(self,attr)
        except AttributeError:
            if self._esky_lazy_target is _LazyImport:
                self._esky_lazy_load()
            return getattr(self._esky_lazy_target,attr)

    def __bool__(self):
        if self._esky_lazy_target is _LazyImport:
            self._esky_lazy_load()
        return bool(self._esky_lazy_target)

def sftp_upload_window_size_set(srv,file, method_to_call='put'):
    '''
    sets config for uploading files with pysftp
    '''
    channel = srv.sftp_client.get_channel()
    channel.lock.acquire()
    channel.out_window_size += os.stat(file).st_size * 1.1   # bit more bytes incase packet loss
    channel.out_buffer_cv.notifyAll()
    channel.lock.release()
