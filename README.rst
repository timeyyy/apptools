
Peasoup Specification
======================

A cross platform desktop application library for python3

We want to provide a collection of common methods used in application deployment, from cli to gui.

Besides providing the library we provide a script that will ask question and generate alot of boiler plate for you.

We want to do this because there is alot of background stuff that is requried to make a good gui program, a new programmer has a rough time sailing these waters, expierenced programmers will come out fine but it could have been cleaner and faster.

We also want to promote growth in this area. There is a billion web frameworks yet really nothing in this area.


What the user gets for free
=============================

- automatically detect if running portably or installed
- put data files in correct location
- set permissions on files
- setup manifest files
- constants such as your app name saved in one place
- uploading error logs to server, setup logging with sensible defaults
- define system tray, title bar, global hotkeys
- easy to use config file for system info
- autostart on system load
- setup Readme, license, git, testing, etc, promote good programming practices


Future
=======
The main reason this specifcation exists is so we don't shoot ourselves in the foot in the future.
    - i feel this needs to be written really well ( the program), extendability is key to get others contributing and having a project that encompasses alot of feature and just works!
some options we chould support would be 
    - make a end to end test suite ( for the users application which is customized from the setup options)
    - provide a script for packaging, uploading to server, rolling out new versions etc


Sample
======

> Enter Name
...test app

> Which platforms do you want to support?
... osx mac windows

> Gui or Cli
...gui

> which gui library are you using?
...tkinter

> Do you want to add build options for windows?
...y

> would you like to add automatic updating using esky
... y

> which freezer would you like to use for windows?
... cxfreeze


Conclusion
==========

I think a strong side benifet of such an app would be that it would help newbies and kids really get some cool results fast.
If people can make some simple game and bundle it quickly and start showing their friends i feel it will help give python a big boost in popularity. 

implementation
==============
Seems like `bob the builder<https://github.com/iElectric/mr.bob>`_ is perfect for building our ccli questions and resulting templates. 

Seems like `Scons <http://www.scons.org/>`_ and `pybuilder <https://github.com/pybuilder/pybuilder>`_ are perfect for automating our tests/linters/deploy


gui (other stuff)
==================
This is probably out of this scope but anyway..


We have alot of different options with gui these days. You may opt to:
 - use your gui as is
 - use a helper library 
 - use a gui to spit out your code. 
   
There is alot of diversity.. There exists so many libraries that people make and drop.. tkhappy, breezygui, tkrad, etc etc

There is almost always a lack of community made gui widgets that we can use.
Or maybe you like this cool graph thing in wxwidgets but someone has made xyz for tkinter..

our solution to this is to try and promote a way to sepearte the logic and the gui. In doing so we enable code reuse!


Provide a standard for:
 - writing cross platform gui elements, 
 - user api 
 - develper api (for extending etc)

The main reason for doing this is so that we can program high level stuff for easy, in this library we might provide a default gui for restarting your app for intance, or you can plug your on in.

