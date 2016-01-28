import os 
import sys
import subprocess
import logging

from peasoup.util import lazy_import

@lazy_import
def esky():
    import esky
    return esky

class Restarter():
    '''Easily restart script or frozen apps'''

    def start(self):
        self.app_restart()

    @classmethod
    def app_restart(cls):
        '''
        Restart a frozen esky app
        Can also restart if the program is being run as a script
        passes restarted as an argument to the restarted app
        '''
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
        '''
        return esky.util.appdir_from_executable(sys.executable)
