# Copyright 2015 Timothy C Eichler (c) , All rights reserved.
# Restrictive license being used whereby the following apply.
# 1. Non-commercial use only
# 2. Cannot modify source-code for any purpose (cannot create derivative works)
# The full license can be viewed at the link below
# http://www.binpress.com/license/view/l/9dfa4dbfe85c336d16d1dd71a2e2cfb2

#!/usr/bin/env python3
import subprocess    
import time  
import os
import getpass

import psutil
from timstools import only_numerics

if os.name == 'nt':
    import win32gui
    import win32process
    import win32con

def process_exists(pid=None):
    """
    Evaluates a Pid Value defaults to the currently foucsed window
    against the current open programs,
    if there is a match returns the process name and pid
    otherwise returns None, None
    """
    if not pid:
        pid = current_pid()
    elif callable(pid):
        pid = pid()

    if pid and psutil.pid_exists(pid):
        pname = psutil.Process(pid).name()
        if os.name == 'nt':
            return os.path.splitext(pname)[0], pid
        return pname, pid
    return None, None


def get_window_id(): #used by xdotool, good idea to save as reference   #this is window id of currently focused window
    cmd=['xdotool','getactivewindow']        # Gives a unique window id which we will use to get our PID    #TBD this method meant to be better supposingly, trying it out if no errors we all good
    #~ cmd=['xdotool','getwindowfocus']        # Gives a unique window id which we will use to get our PID
    args = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    #out=(args.stdout.read())
    args=str(args[0])                       # Just take the output not the errors from the tuple
    args=only_numerics(args)                # gives us only numerical numbers
    return args

def current_pid():
    if os.name == 'nt':
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
    else:
        window_id = get_window_id()
        cmd=["xdotool","getwindowpid", window_id]   # Uses the Window Id to find the PID
        args = subprocess.Popen(cmd,stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
        pid = args[0].decode('utf-8')
        #~ pid = only_numerics(args)         # Our Pid of the Currently focused Window at time of function call
    try:
        return int(pid) 
    except (ValueError, TypeError): 
        return None

def moveWindow(window_id,x,y):
    """
    Moves a window to a given position given the window_id and absolute co ordinates,
    --sync option auto passed in, will wait until actually moved before giving  control back to us
    """
    #~ cmd=['xdotool','windowmap', Holder.data]   # Command to set window focus
    cmd=['xdotool','windowmove', ('%s %s %s') % (window_id,x,y)]   # Command to move window
    args = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    print(args[1])
    #args=str(args[0])                      # Just take the output not the errors from the tuple
    #args=only_numerics(args) 

#~ import platform
#~ print(platform.node())

from socket import gethostname
    
def listpid(toggle='basic'): # Add method to exclude elements from list
    '''list pids'''
    proc=psutil.process_iter()# evalute if its better to keep one instance of this or generate here?
    if toggle=='basic':
        host=gethostname()
        host2=os.getenv('HOME').split(sep='/'   )[-1]
        for row in proc:
            #~ DPRINT([row.ppid(),row.name(),host],'username,row.name,host')
            if row.username() in host or row.username() in host2:   #new psutil using grabing timeyyy and not alfa for username so host 2 is getting the timeyyy on UBUNTU  
                yield row.name(), row.ppid()
    elif toggle=='all':
        for row in proc:
            
            yield row.name(), row.ppid()
    elif toggle =='windows-basic':
        for row in proc:
            try:
                pname = psutil.Process(row.pid).name()
                pname = pname[:-4]#removiing .exe from end
                yield pname, row.pid
            except:
                pass#cannot get info on system proccessors, returns exception

    #~ for proc in psutil.process_iter():
        #~ try:
            #~ print (proc.pid, proc.username)
#~ 
        #~ except psutil.AccessDenied:
            #~ print("denied")
    #~ 

def show_window(value):
    if os.name == 'nt':
        HWND = value
        win32gui.ShowWindow(HWND, win32con.SW_RESTORE)
        win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0,0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE )
        win32gui.SetWindowPos(HWND,win32con.HWND_TOPMOST, 0, 0, 0,0,win32con.SWP_NOMOVE + win32con.SWP_NOSIZE )
        win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0,0,win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        #~ win32gui.ShowWindow(hWnd,win32con.SW_SHOW); 
        #~ win32gui.BringWindowToTop(hWnd);
        #~ win32gui.SetForegroundWindow(hWnd);
        #http://stackoverflow.com/questions/6312627/windows-7-how-to-bring-a-window-to-the-front-no-matter-what-other-window-has-fo
        #http://timgolden.me.uk/pywin32-docs/win32gui__SetWindowPos_meth.html
        #~ //-- on Windows 7, this workaround brings window to top
        #~ win32gui.SetWindowPos(hWnd,HWND_NOTOPMOST,0,0,0,0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE);
        #~ win32gui.SetWindowPos(hWnd,HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE | win32con.SWP_NOSIZE);
        #~ win32gui.SetWindowPos(hWnd,HWND_NOTOPMOST,0,0,0,0,win32con.SWP_SHOWWINDOW | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE);
    else:
        name = value
        cmd = ['xdotool','search','--name','--onlyvisible', name,'windowactivate']
        args = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    
def get_hwnds_for_pid (pid):
    def callback (hwnd, hwnds):
        #~ if win32gui.IsWindowVisible (hwnd) and win32gui.IsWindowEnabled (hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId (hwnd)
        if found_pid == pid:
            hwnds.append (hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows (callback, hwnds)
    return hwnds

def get_active_title():
    '''returns the window title of the active window'''
    if os.name == 'posix':
        cmd = ['xdotool','getactivewindow','getwindowname']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        title = proc.communicate()[0].decode('utf-8')
    else:
        raise NotImplementedError
    return title

def get_processes():
    '''returns process names owned by the user'''
    user = getpass.getuser()
    for proc in  psutil.process_iter():
        if proc.username() != user:
            continue
        pname = psutil.Process(proc.pid).name()
        if os.name == 'nt':
            pname = pname[:-4]          # removiing .exe from end
        yield pname

def get_titles():
    '''returns titles of all open windows'''
    if os.name == 'posix':
        for proc in get_processes():
            cmd = ['xdotool','search','--name', proc]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            window_ids = proc.communicate()[0].decode('utf-8')
            if window_ids:
                for window_id in window_ids.split('\n'):
                    cmd = ['xdotool','getwindowname',window_id]
                    proc = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                    title = proc.communicate()[0].decode('utf-8')
                    try:
                        if title[-1] == '\n':
                            title = title[:-1]
                        yield title
                    except IndexError:
                        pass
    else:
        raise NotImplementedError

if __name__ == '__main__':
    
    from pprint import pprint
    pprint(list(get_titles()))
    # print(get_titles())
    pass
    #~ foregroundWindow('Mozilla Firefox')


#im using xdo alot, wmctrl used by txkert       
#try xdotool http://www.semicomplete.com/projects/xdotool/xdotool.xhtml#window_commands
#replacement for xdo http://tomas.styblo.name/wmctrl/
    
    #~ pid_table = psutil.process_iter()
    #~ genPidL=pidList(pid_table)
    #~ pidList(pid_table)
    
    """                     # Test methods of host name
    import platform
    print(platform.node())
    import socket
    print(socket.gethostname())
    """

    


