# Copyright 2015 Timothy C Eichler (c) , All rights reserved.
'''
see design spec
'''
import os
import sys
import platform
import time
import inspect
import logging

from timstools import ignored as suppress

from peasoup import pidutil       # Todo delete this after done integrating get pid
from peasoup.util import lazy_import
from peasoup.uploadlogs import LogUploader

@lazy_import
def json():
    import json
    return json

@lazy_import
def yaml():
    import yaml
    return yaml

@lazy_import
def esky():
    import esky
    return esky

if os.name == 'nt':
    import win32security
    import ntsecuritycon as con
    import win32api
    import pywintypes

PEASOUP_USER_DIR = 'autobots'
PEASOUP_CONFIG_FILE = 'config.json'

class CfgDict(dict):
    '''
    Because json is alwasy going to give us a normal dict we have to
    add some new mothods after the fact,
    This is a collection of methods for our config dict
    Pass in the old dict and wrap on some shiny new methods

    This is jus like a decorator but i'm not using the 
    explict syntax on it #TODO
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

class AppBuilder(LogUploader):

    '''
    Add functions to the dictionary -> self.shutdown_cleanup
    the functions will be run on cleanup, if you choose not, to use
    the shutdown function and use the check_if_open function you will
    need to run the functions in self.shutdown_cleanup on shutdown

    main file is required to get the abspath of the script
    '''

    def __init__(self, main_file):
        AppBuilder.main_file = main_file
        self.pcfg = self.get_pcfg()
        self.app_name = self.pcfg['app_name']
        self.shutdown_cleanup = {}
        self.start_time = time.time()

    @staticmethod
    def get_pcfg():
        '''
        sets up the config options by reading globals saved in peasoup/global.py
        as self.pcfg
        '''
        path = os.path.dirname(AppBuilder.main_file)
        file = os.path.join(path,
                            PEASOUP_USER_DIR,
                            PEASOUP_CONFIG_FILE)
        print(file)
        with open(file) as f:
            pcfg = json.load(f)
        return pcfg

    def create_cfg(self, cfg_file, defaults=None, mode='json'):
        '''
        set mode to json or yaml? probably remove this option..Todo

        Creates the config file for your app with default values
        The file will only be created if it doesn't exits

        also sets up the first_run attribute.
        
        also sets correct windows permissions

        you can add custom stuff to the config by doing
        app.cfg['fkdsfa'] = 'fdsaf'
        # todo auto save on change
        remember to call cfg.save()

        '''
        assert mode in ('json', 'yaml')
        self.cfg_mode = mode
        self.cfg_file = cfg_file
        try:
            self.cfg = CfgDict(app=self, cfg=self.load_cfg())
            logging.info('cfg file found : %s' % self.cfg_file)
        except FileNotFoundError:
            self.cfg = CfgDict(app=self, cfg={'first_run': True})
            with suppress(TypeError):
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
        logging.info('Checking if our app is already Open')
        if not path and self.cfg:
            self._check_if_open_using_config()
        elif path:
            if appdata:
                file = path.split(os.sep)[-1]
                self.check_file = self.uac_bypass(file=file)
            else:
                self.check_file = path
            self._check_if_open_using_path()

        self.shutdown_cleanup['release_singleton'] = self.release_singleton

    def release_singleton(self):
        '''deletes the data that lets our program know if it is
        running as singleton when calling check_if_open,
        i.e check_if_open will return fals after calling this
       '''
        with suppress(KeyError):
            del self.cfg['is_programming_running_info']
        with suppress(FileNotFoundError, AttributeError):
            os.remove(self.check_file)


    def _check_if_open_using_config(self):
        key = 'is_programming_running_info'
        try:
            values = self.cfg[key]
            if os.name == 'posix':
                old_pid = values[0]
            else:
                logging.info(str(values))
                old_pid, hwnd = values
            name, exists = pidutil.process_exists(int(old_pid))
            if exists:
                # Todo, the checks with the name part haven't been tested
                if self.is_installed() and self.pcfg['app_name'] not in name:
                    _raise = True
                elif not self.is_installed() and 'python' not in name.lower():
                    _raise = True
                else:
                    _raise = False

                if _raise:
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
                sys.exit(800)

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
        session_time = round((time.time() - self.start_time)/60, 0)
        logging.info('session time: {0} minutes'.format(session_time))
        logging.info('End..')

    @staticmethod
    def rel_path(*file_path):
        '''
        gives relative paths to files, works when frozen or unfrozen
        to get the root path just pass in the string __file__
        '''
        if hasattr(sys, 'frozen'):
            if file_path[0] == '__file__':
                return sys.executable
            return os.path.join(os.path.dirname(sys.executable), *file_path)
        else:
            try:
                main_file = AppBuilder.main_file
            except AttributeError:
                # The first call setting up the instance
                main_file = inspect.stack()[1][1]
            if file_path[0] == '__file__':
                print(os.path.realpath(main_file))
                return os.path.realpath(main_file)
            return os.path.join(os.path.dirname(main_file), *file_path)

def setup_logger(log_file):
    '''One function call to set up logging with some nice logs about the machine'''
    cfg = AppBuilder.get_pcfg()
    logger = cfg['log_module']
    # todo make sure structlog is compliant and that logbook is also the correct name???
    assert logger in ("logging", "logbook", "structlog"), 'bad logger specified'
    exec("import {0};logging = {0}".format(logger))

    AppBuilder.logger = logging

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
    #Todo rename this to allow_all, also make international not just for english..
    if os.name == 'nt':
        try:
            everyone, domain, type = win32security.LookupAccountName(
            "", "Everyone")
        except Exception:
            # Todo fails on non english langauge systesm ... FU WINDOWS
            # Just allow permission for the current user then...
            everyone, domain, type = win32security.LookupAccountName ("", win32api.GetUserName())
        # ~ user, domain, type = win32security.LookupAccountName ("", win32api.GetUserName())
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


def setup_raven():
    '''we setup sentry to get all stuff from our logs'''
    pcfg = AppBuilder.get_pcfg()
    from raven.handlers.logging import SentryHandler
    from raven import Client
    from raven.conf import setup_logging
    client = Client(pcfg['raven_dsn'])
    handler = SentryHandler(client)
    # TODO VERIFY THIS -> This is the way to do it if you have a paid account, each log call is an event so this isn't going to work for free accounts...
    handler.setLevel(pcfg["raven_loglevel"])
    setup_logging(handler)
    return client


