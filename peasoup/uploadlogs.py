
from time import gmtime, strftime
from contextlib import suppress
from base64 import b64decode as crypto
import codecs

from peasoup.util import lazy_import

@lazy_import
def traceback():
    import traceback
    return traceback

@lazy_import
def threading():
    import threading
    return threading

@lazy_import
def os():
    import os
    return os


import tkquick.gui.maker as maker
from peasoup.gui import uploader as gui_uploader
import tkinter.ttk as ttk
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
        traceback.print_exc()
        if logger: 
            logger.exception('Unexpected runtime Error...')
        else:
            self.logger.exception('Unexpected runtime Error...')

    def upload_logs(self, release_singleton=True):
        '''
        uploads a log to a server using the method and gui specifed
        in self.pcfg
        singleton mode can be disabled so a new version can be restarted whille uploading oges
        on typicallin in the case of uploadnig after a crash or sys exit
        set self.cfg log_upload_interface to gui/cli/or background
        '''
        if release_singleton:
            self.release_singleton()

        def _upload():
            for log in self.get_logs():
                new_name = self._uniquename(log)
                self._upload(log, new_name)
                # Todo: keep log around for a few days
                self.delete_log(log)

        if self.pcfg['log_server_interface'] == 'gui':
            raise NotImplementedError
            threading.Thread(target=threadme)
            gui_uploader(threadme)
        elif self.pcfg['log_server_interface'] == 'cli':
            raise NotImplementedError
        elif self.pcfg['log_server_interface'] == 'background':
            _upload()

    def delete_log(self, log):
        '''check we don't delte anythin unintended'''
        if os.path.splitext(log)[-1] != '.log':
            raise Exception('File without .log was passed in for deletoin')
        with suppress(Exception):
            os.remove(log)


    def get_logs(self):
        '''returns logs from disk, requires .log extenstion'''
        folder = os.path.dirname(self.pcfg['log_file'])
        for path, dir, files in os.walk(folder):
            for file in files:
                if os.path.splitext(file)[-1] == '.log':
                    yield os.path.join(path, file)

    # TODO MAKE THIS TAKE THE TIME FROM THE LOG IMPORTANT
    def _uniquename(self, log):
        '''
        renames the log to ensure we get no clashes on the server
        subclass this to change the path etc'''
        return '{hostname} - {time}.log'.format(
                                hostname=os.getenv('USERNAME'),
                                time=strftime("%a, %d %b %Y %H-%M-%S", gmtime()))

    def _upload(self, log, new_name):
        if self.pcfg['log_server_method'] == 'sftp':
            import pysftp
            from peasoup.util import sftp_upload_window_size_set
            try:
                srv = pysftp.Connection(host=self.pcfg['log_server_host'],
                                        username=self.pcfg['log_server_username'],
                                        password=self.rot13(self.pcfg['log_server_password']),
                                        port=self.pcfg['log_server_port'])
                self.logger.info(
                        'Uploading log to server %s' % self.pcfg['log_server_host'])
                sftp_upload_window_size_set(srv, log)
                srv.put(log, new_name)
            except pysftp.ConnectionException:
                raise pysftp.ConnectionError('Could not connecto to log server')
            finally:
                with suppress(UnboundLocalError):
                    srv.close()
        else:
            # need to implement the gui uploaders...
            raise NotImplementedError

    def release_singleton(self):
        raise NotImplementedError('Please subclass')

    def rot13(self, encrypyted):
        ''' Very secure encryption (ceaser used it), apply it multiple times'''
        def random():
            # guarnteed random from fair dice roll
            return 4
        return codecs.encode(
                        codecs.encode(
                                crypto(encrypyted).decode(),
                                'rot_{amount}'.format(amount=int(52/random()))),
                        'rot_{salt}'.format(salt=int(52/random())))

def add_date(log):
    '''Userful for randomizing the name of a log'''
    return '{base} - {time}.log'.format(
			base=os.path.splitext(log)[0],
			time=strftime("%a, %d %b %Y %H-%M-%S", gmtime()))


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
