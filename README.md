
              mmm,
             /::* > -Chit Chat!
    \        |::/
     Aaa..../:::\\
     \:::::::::::|
      \:::::::::/
       \:::::::/
         \:/\:/
          |_  \__
-----------------------------------------
Welcome to the HEveNtful chat server!
-----------------------------------------

## Functionality:

* Users authenticate themselves with a unique name before being able to write messages

* Users can signal their status ("Online", "Away" and "DND") to other users

* Messages can be sent to unique users, or to all connected users in the chat

* All connected users can be listed with their current states

* All users get a notification when a user connects or disconnects


## Installing dependencies (tested on OSX)

> brew install libevent

> pip install cython

> hg clone https://bitbucket.org/denis/gevent

> cd gevent

> python setup.py build

> python setup.py install


## Usage

To start the server (default port is 6000):
> python server.py [port]

To connect to the server:
> telnet hostname 6000

Registered users:

* magnus:qwerty

* svea:frog

* bobby:12345

