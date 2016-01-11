#~ Copyright 2015 Timothy C Eichler (c) , All rights reserved.
'''
see design spec 
'''
import os
import sys
import platform
import logging
import platform
import shutil
import traceback
# all these here are for upload log file
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import _thread as thread
import queue
import json
from contextlib import suppress
from pprint import pprint

try:
    import yaml
except ImportError:
    pass
import tkquick.gui.maker as maker
from timstools import parent_path, ignored

if os.name == 'nt':
    import win32security
    import ntsecuritycon as con
    import win32api
    import pywintypes
try:
    from . import pidutil       # delete this after done integrating get pid
except ImportError:
    from . import pidutil

class CfgDict(dict):
    '''
    Because json is alwasy going to give us a normal dict we have to
    add some new mothods after the fact,
    This is a collection of methods for our config dict
    Pass in the old dict and wrap on some shiny new methods
    '''
    def __init__(self, app, cfg):
        super().__init__(self, **cfg)
        self.app = app

    def __getattribute__(self, item):
        if item == 'save':
            return lambda: CfgDict.save(self)
        else:
            return object.__getattribute__(self, item)

    # TODO To be honest i have no F*** what is going on here but it works, how to remove this self.app state...
    def save(self):
        '''saves our config objet to file'''
        if self.app.cfg_mode == 'json':
            with open(self.app.cfg_file, 'w') as opened_file:
                json.dump(self.app.cfg, opened_file)
        else:
            with open(self.app.cfg_file, 'w')as opened_file:
                yaml.dump(self.app.cfg, opened_file)

class AppBuilder():

    '''
    Add functions to the dictionary -> self.shutdown_cleanup
    the functions will be run on cleanup, if you choose not, to use
    the shutdown function and use the check_if_open function you will
    need to run the functions in self.shutdown_cleanup on shutdown
    '''

    def __init__(self, name):
        self.app_name = name
        self.shutdown_cleanup = {}

    
    def create_cfg(self, cfg_file, defaults=None, mode='json'):
        '''
        # todo should be able to habe multiple cfgs active, such as usercfg?
        set mode to json or yaml

        Creates the config file for your app with default values
        The file will only be created if it doesn't exits

        also sets up the first_run attribute.
        
        also sets correct windows permissions

        you can add custom stuff to the config by doing
        app.cfg['fkdsfa'] = 'fdsaf'
        # todo auto save on change
        remember to call app.cfg.save()

        '''
        assert mode in ('json', 'yaml')
        self.cfg_mode = mode
        self.cfg_file = cfg_file
        try:
            self.cfg = CfgDict(app=self, cfg=self.load_cfg())
            logging.info('cfg file found : %s' % self.cfg_file)
        except FileNotFoundError:
            self.cfg = CfgDict(app=self, cfg={'first_run': True})
            with ignored(TypeError):
                self.cfg.update(defaults)
            self.cfg.save()
            set_windows_permissions(self.cfg_file)
            logging.info(
                'Created cfg file for first time!: %s' %
                self.cfg_file)

        if self._check_first_run():
            self.first_run = True
        else:
            self.first_run = False

    def load_cfg(self):
        '''loads our config object accessible via self.cfg'''
        if self.cfg_mode == 'json':
            with open(self.cfg_file) as opened_file:
                return json.load(opened_file)
        else:
            with open(self.cfg_file) as ymlfile:
                return yaml.safe_load(ymlfile)


    def _check_first_run(self):
        '''
        Checks if this is the first time our app is being run
        This is called automatically when using create_cfg()
        use then app.first_run attribute to check for True or False
        '''
        if self.cfg['first_run']:
            self.cfg['first_run'] = False
            self.cfg.save()
            return True
        else:
            return False

    def is_installed(self):
        '''If the program is fully installed returns 1
        Only invoked if the program is being run from Program Files     #Tbd make this more robust
        '''
        if os.name == 'nt':
            # tbd find a better way to tell if  a program is installed in
            # registry
            if 'Program Files' in os.getcwd():
                return 1
            else:
                return 0
        else:
            print('TBD LINUX CHECK FULLY INSTLALED APPTOOLS')
            return 0

    # http://stackoverflow.com/questions/16872448/c-sharp-write-and-read-appsettings-and-log-files-best-practice-uac-program-file
    def uac_bypass(self, file=None, create=False, overwrite=False):
        '''
        path = uac_bypass(file)

        This function will only operate when your program is installed
        check the is_installed function for details

        Moves working data to another folder. The idea is to get around
        security and uac on windows vista +

        returns cwd on linux, windows returns path with write
        access: C:\\ProgramData\\appname here

        if a file is passed in it will be appended to the path

        set create to true to create the file in the programData folder

        setting overwrite to True will silently overwrite, otherwise a
        FileExistsError is raised

        Setting overwrite to get, will get the file path instead of throwing an error

                                ---Background----
        If a user is using windows, Read write access is restriced in the
        Program Files directory without prompting for uac.

        We create a folder in c:\Program Data\ of the program name and
        save logging data etc there.

        This way the program doesnt need admin rights.

        '''
        if self.is_installed():
            if os.name == 'nt':
                # tbd check if xp returns this also note htis is not required
                # for xp admin security stuff its just a consitancy thing..
                if platform.win32_ver()[0] == 'xp':
                    path = os.path.join(
                        'C:',
                        'Documents and Settings',
                        os.getenv('USERNAME'),
                        'Application Data',
                        self.app_name)
                else:
                    path = os.path.join(r'C:\ProgramData', self.app_name)
                os.makedirs(path, exist_ok=True)
        else:
            path = os.getcwd()

        if create:
            logging.info(
                'Uac Bypass - Attempting to Create: %s' %
                os.path.join(
                    path,
                    file))
            TO = os.path.join(path, file)
            if overwrite and overwrite != 'get':
                new_file = open(TO, 'w')
                new_file.close()
            elif not os.path.exists(TO):
                new_file = open(TO, 'w')
                new_file.close()
            elif overwrite != 'get':
                raise FileExistsError
        if not file:
            return path
        else:
            return os.path.join(path, file)

    def check_if_open(self, path=None, appdata=False, verbose=False):
        '''
        Allows only one version of the app to be open at a time.

        If you are calling create_cfg() before calling this,
        you don't need to give a path. Otherwise a file path must be
        given so we can save our file there.

        Set appdata to True to run uac_bypass on the path, otherwise
        leave it as False
        '''
        #~ To know if the system crashed, or if the prgram was exited smoothly
        #~ turn verbose to True and the function will return a named tuple  # TBD
        #~ if os.name == 'nt':
        #~ hwnd = int(self.root.wm_frame(),0)
        #~ #saving a hwnd reference so we can check if we still open later on
        #~ with open (self.check_file,'a') as f:
        #~ f.write(str(hwnd))
        #~ logging.info('adding hwnd to running info :'+str(hwnd))
        #~
        logging.info('Checking if A window is already Open')
        if not path and self.cfg:
            self._check_if_open_using_config()
        elif path:
            if appdata:
                file = path.split(os.sep)[-1]
                self.check_file = self.uac_bypass(file=file)
            else:
                self.check_file = path
            self._check_if_open_using_path()

        def cleanup():
            # These have to be removed for us to know if its closed
            with suppress(KeyError):
                del self.cfg['is_programming_running_info']
            with suppress(FileNotFoundError, AttributeError):
                os.remove(self.check_file)

        self.shutdown_cleanup['remove_check_if_open_flag'] = cleanup

    def _check_if_open_using_config(self):
        key = 'is_programming_running_info'
        logging.info('holy shit')
        try:
            values = self.cfg[key]
            if os.name == 'posix':
                old_pid = values[0]
            else:
                logging.info(str(values))
                old_pid, hwnd = values
            name, exists = pidutil.process_exists(int(old_pid))
            if not exists:
                logging.info('DOESNT EXIST')
                del self.cfg[key]
                self.cfg.save()
                logging.debug(
                    'Last time the program ran it didn\'t close properly')
                raise KeyError
            else:
                logging.debug('Loading the program as it\'s already running')
                if os.name == 'posix':
                    pidutil.show_window(self.app_name)
                if os.name == 'nt':
                    hwnd = pywintypes.HANDLE(int(hwnd))
                    pidutil.show_window(hwnd)
                logging.info('Exiting new instance of our program')
            sys.exit()

        except(KeyError, ValueError):
            # Start program normally
            self.cfg[key] = [os.getpid()]
            self.cfg.save()
            if os.name == 'nt':
                def add_hwnd():
                    hwnd = self.get_windows_hwnd()
                    self.cfg[key].append(self.get_windows_hwnd())
                    self.cfg.save()
                self.root.after(1000, add_hwnd)

    def _check_if_open_using_path(self):
        try:
            with open(self.check_file, "r") as f:
                old_pid = f.readline()
                name, exists = pidutil.process_exists(int(old_pid))
                logging.debug(
                    'name of process gotten ,old_pid : {0} {1}  '.format(
                        name,
                        old_pid))
                if not exists:
                    f.close()
                    os.remove(self.check_file)
                    logging.debug('The old program is not runnning anymore')
                    raise FileNotFoundError
                else:
                    logging.debug(
                        'Loading the program as it\'s already running')
                    if os.name == 'posix':
                        pidutil.show_window(self.app_name)
                    if os.name == 'nt':
                        hwnd = f.readline()
                        logging.debug('hwnd from file ' + str(hwnd))
                        hwnd = pywintypes.HANDLE(int(hwnd))
                        pidutil.show_window(hwnd)
                    logging.info('Exiting new instance of our program')
                sys.exit()
        # Open as Normal
        except FileNotFoundError:
            with open(self.check_file, 'w') as f:
                f.write(str(os.getpid()) + '\n')
                if os.name == 'nt':
                    def add_hwnd():
                        with open(self.check_file, 'a') as f:
                            hwnd = self.get_windows_hwnd()  # FUCK U doesn't run in a function 
                            logging.info('writing hwnd '+ str(hwnd))
                            f.write(str(hwnd) + '\n')
                    self.root.after(2000, add_hwnd)
                set_windows_permissions(self.check_file)

    def get_windows_hwnd(self):
        '''Right now only knows how to get hwnd for a tkinter application,
        if the program is not yet running you will need to use
        the tkinter after method'''
        return int(self.root.wm_frame(), 0)

    def shutdown(self):
        ''' shutdown operations on exit, this is run by
        a finaly statement after the tkinter mainloop ends
        call root.quit to get here,
        Note you will still need to call sys.exit()
        '''
        logging.info('Shutdown procedures being run!')
        for func in self.shutdown_cleanup.values():
            func()
        logging.info('End..')

    @classmethod
    def app_restart(cls):
        '''
        Restart a frozen esky app
        Can also restart if the program is being run as a script
        passes restarted as an argument to the restarted app
        '''
        import subprocess #TODO MOVE?
        logging.debug('In restarter')
        executable = sys.executable.split(os.sep)[-1]
        if os.name == 'nt':
            logging.info('executable is is %s' % executable)
            # restart works here when testing compiled version only
            if executable != 'python.exe':
                boot_strap_path = cls.esky_bootstrap_path()
                bootstrap_file = os.path.join(boot_strap_path, executable)
                logging.info('Bootstrap file for restart: %s' % bootstrap_file)

                subprocess.Popen(
                    [os.path.join(bootstrap_file, bootstrap_file), 'restarted'])
        #~ os.execl(bootstrap_file, bootstrap_file, * sys.argv)     # TBD make this work This restarts our process and doesn't return, for somet reason the new restarted version is the old and all fucked

    @staticmethod
    def esky_bootstrap_path():
        '''
        returns the executable path

        the esky path is either one or two directories up, depending on the update
        status of our app. returns the toplevel directory where the executable lives

        C:\\Program Files (x86)\\Uncrumpled             Before Updated
        C:\\Program Files (x86)\\Uncrumpled\appdata     After updated
        '''
        if hasattr(sys, 'frozen'):
            if os.path.basename(parent_path(os.getcwd())) == 'appdata':
                esky_path = parent_path(os.getcwd(), 2)
            else:
                esky_path = parent_path(os.getcwd(), 1)
            return esky_path
        else:
            return os.path.dirname(sys.executable)


def setup_logger(log_file):
    '''One function call to set up logging with some nice logs about the machine'''
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s: %(message)s')  # one run
    logging.debug('System is: %s' % platform.platform())
    logging.debug('Python archetecture is: %s' % platform.architecture()[0])
    logging.debug('Machine archetecture is: %s' % platform.machine())

    set_windows_permissions(log_file)


def set_windows_permissions(filename):
    '''
    At least on windows 7 if a file is created on an Admin account,
    Other users will not be given execute or full control.
    However if a user creates the file himself it will work...
    So just always change permissions after creating a file on windows

    Change the permissions for Allusers of the application
    The Everyone Group
    Full access

    http://timgolden.me.uk/python/win32_how_do_i/add-security-to-a-file.html
    '''
    if os.name == 'nt':
        everyone, domain, type = win32security.LookupAccountName(
            "", "Everyone")
        #~ user, domain, type = win32security.LookupAccountName ("", win32api.GetUserName())
        #~ userx, domain, type = win32security.LookupAccountName ("", "User")
        #~ usery, domain, type = win32security.LookupAccountName ("", "User Y")

        sd = win32security.GetFileSecurity(
            filename,
            win32security.DACL_SECURITY_INFORMATION)
        # instead of dacl = win32security.ACL()
        dacl = sd.GetSecurityDescriptorDacl()

        #~ dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE, everyone)
        #~ dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user)
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            con.FILE_ALL_ACCESS,
            everyone)

        sd.SetSecurityDescriptorDacl(1, dacl, 0)   # may not be necessary
        win32security.SetFileSecurity(
            filename,
            win32security.DACL_SECURITY_INFORMATION,
            sd)


# TBD THIS IS TKINTER SPECIF SO MOVE IT OUT!
def handle_fatal_exception(
        error,
        restarter,
        file,
        host,
        username,
        password,
        port,
        pre_restarter='gui',
        output=None):
    '''
    uploads a log to a server
    displays a progress widget using tktiner
    restart function is required in the case of the user wanting to restart
    '''
    def upload_log():
        # this is run in a thread
        nonlocal output
        import pysftp
        from time import gmtime, strftime
        from timstools import sftp_upload_window_size_set
        try:
            srv = pysftp.Connection(host=host, username=username, password=password, port=port)
            logging.info('Uploading log to server')
            sftp_upload_window_size_set(srv, file)
            if not output:
                output = os.getenv(
                    'USERNAME') + '-' + strftime("%a, %d %b %Y %H-%M-%S", gmtime()) + '.log'
            srv.put(file, output)
        except pysftp.ConnectionException:
            pass
        finally:
            with suppress(UnboundLocalError):
                srv.close()
            tkinter_queue.put(root.quit)

    def poll_tkinter_queue():
        # tktiner after method not avaliable from other threads!,
        # this runs functions put on the queue
        try:
            func = tkinter_queue.get(block=False)
        except queue.Empty:
            pass
        else:
            func()
        root.after(100, poll_tkinter_queue)

    import traceback
    print()
    traceback.print_exc()
    logging.exception('Unexpected runtime Error Occured')
    root = tk.Tk()
    root.withdraw()
    
    tkinter_queue = queue.Queue()
    thread.start_new_thread(upload_log, ())
    root.after(100, poll_tkinter_queue)
    #~ ttk.Label(root, text='Uploading error logs! please wait...').pack()
    #~ prog = ttk.Progressbar(root, mode='indeterminate', length=100)
    #~ prog.pack()
    #~ prog.start()
    #~ maker.center_window(root, 100, 20)
    #~ root.deiconify()
    root.mainloop()

    if pre_resstarter == 'gui':
        if messagebox.askyesno(
                'Unexpected Error',
                ' Sorry for the inconvienience. Would you like to restart?',
                parent=root):

            logging.debug('running restarter function')
            restarter()
    else:
        print('TODO custom pre restart')
        # pre_restarter()
        # restart()


class TkErrorCatcher:  # Tbd move this code elsewhere

    '''
    Enables the program to handle errors caused in events
    without tktiner muting them and only printing the traceback.
    '''

    def __init__(self, func, subst, widget):
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except SystemExit as msg:
            raise SystemExit(msg)
        except Exception as err:
            raise err
            #~ traceback.print_exc(file=open('test.log', 'a'))
