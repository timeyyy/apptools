
from peasoup.util import lazy_import

from time import gmtime, strftime
from contextlib import suppress
from base64 import b64decode as crypto


@lazy_import
def traceback():
    import traceback
    return traceback

@lazy_import
def thread():
    import _thread as thread
    return thread

import queue

@lazy_import
def os():
    import os
    return os


import tkquick.gui.maker as maker
from peasoup.gui import uploader as gui_uploader

import tkinter.ttk as ttk
# TBD THIS IS TKINTER SPECIF SO MOVE IT OUT!
from peasoup.gui import uploader as gui_uploader

class LogUploader():
    def logexception(self, logger=None):
        '''
        calls exception method on a loger and prints the log to stdout
        logger is set in the cfg
        #Todo more details here on the cfg etc
        :param logger:
        :return:
        '''
        logger.exception('Unexpected runtime Error...')
        traceback.print_exc()

    def upload_logs(self, release_singleton=True):
        '''
        uploads a log to a server using the method and gui specifed
        in self.pcfg
        singleton mode can be disabled so a new version can be restarted whille uploading oges
        on typicallin in the case of uploadnig after a crash or sys exit
        set self.cfg upload_interface to gui/cli/or background
        '''
        if release_singleton:
            raise NotImplementedError
            # Todo self.peasoup.cfg.r
            pass

        def threadme():
            for log in self.getlogs():
                new_name = self.uniquename(log)
                self._upload(log, new_name)
                # To do: keep log around for a few days
                os.remove(log)

        if self.pcfg['upload_interface'] == 'gui':
            gui_uploader(threadme)
        elif self.pcfg['upload_interface'] == 'cli':
            raise NotImplementedError
        elif self.pcfg['upload_interface'] == 'background':
            thread.start_new_thread(threadme, '',)

    def getlogs(self):
        '''returns logs from disk'''
        folder = os.path.dirname(self.pcfg['log_file'])
        for path, dir, files in os.scandir(folder):
            for file in files:
                yield os.path.join(path, file)

    def uniquename(self, log):
        '''
        renames the log to ensure we get no clashes on the server
        subclass this to change the path etc'''
        return '{hostname} - {time}.log'.format(
                                hostname=os.getenv('USERNAME'),
                               time=strftime("%a, %d %b %Y %H-%M-%S", gmtime()))

    def _upload(self, log, new_name):
        if self.pcfg['upload_method'] == 'sftp':
            import pysftp
            # Todo remove the
            from peasoup.util import sftp_upload_window_size_set
            try:
                srv = pysftp.Connection(host=self.pcfg['log_server_host'],
                                        username=self.pcfg['log_server_name'],
                                        password=self.pcfg['log_server_password'],
                                        port=self.pcfg['log_server_port'])
                self.logger.info(
                        'Uploading log to server %s' % self.pcfg['log_server_name'])
                sftp_upload_window_size_set(srv, log)
                srv.put(log, new_name)
            finally:
                with suppress(UnboundLocalError):
                    srv.close()
        else:
            # need to implement the gui uploaders...
            raise NotImplementedError

    def rot13(self):
        ''' Very secure encryption'''
        return crypto(bytes(self.pcfg['log_server_password']).decode())


# def handle_fatal_exception(
#         error,
#         restarter,
#         file,
#         host,
#         username,
#         password,
#         port,
#         pre_restarter='gui',
#         output=None):
#     '''
#     uploads a log to a server
#     displays a progress widget using tktiner
#     restart function is required in the case of the user wanting to restart
#     '''
#     def upload_log():
#         # this is run in a thread
#         nonlocal output
#         import pysftp
#         from time import gmtime, strftime
#         from timstools import sftp_upload_window_size_set
#         try:
#             srv = pysftp.Connection(host=host, username=username, password=password, port=port)
#             logging.info('Uploading log to server')
#             sftp_upload_window_size_set(srv, file)
#             if not output:
#                 output = os.getenv(
#                         'USERNAME') + '-' + strftime("%a, %d %b %Y %H-%M-%S", gmtime()) + '.log'
#             srv.put(file, output)
#         except pysftp.ConnectionException:
#             pass
#         finally:
#             with suppress(UnboundLocalError):
#                 srv.close()
#             tkinter_queue.put(root.quit)
#
#     def poll_tkinter_queue():
#         # tktiner after method not avaliable from other threads!,
#         # this runs functions put on the queue
#         try:
#             func = tkinter_queue.get(block=False)
#         except queue.Empty:
#             pass
#         else:
#             func()
#         root.after(100, poll_tkinter_queue)
#
#     import traceback
#     print()
#     traceback.print_exc()
#     logging.exception('Unexpected runtime Error Occured')
#     root = tk.Tk()
#     root.withdraw()
#
#     tkinter_queue = queue.Queue()
#     thread.start_new_thread(upload_log, ())
#     root.after(100, poll_tkinter_queue)
#     #~ ttk.Label(root, text='Uploading error logs! please wait...').pack()
#     #~ prog = ttk.Progressbar(root, mode='indeterminate', length=100)
#     #~ prog.pack()
#     #~ prog.start()
#     #~ maker.center_window(root, 100, 20)
#     #~ root.deiconify()
#     root.mainloop()
#
#     if pre_resstarter == 'gui':
#         if messagebox.askyesno(
#                 'Unexpected Error',
#                 ' Sorry for the inconvienience. Would you like to restart?',
#                 parent=root):
#
#             logging.debug('running restarter function')
#             restarter()
#     else:
#         print('TODO custom pre restart')
#         # pre_restarter()
#         # restart()
