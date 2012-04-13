#!/usr/bin/env python
"""
Telnet Chat Server that listens on port 6000.

Connect to it with:
  telnet localhost 6000
"""
import re
import gevent
from gevent.server import StreamServer
import sys

class Status:
    ONLINE = "ONLINE"
    AWAY = "AWAY"
    DND = "DND"

class Client():
    def __init__(self, socket, nick, address):
        self.socket = socket
        self.nick = nick
        self.address = address
        self.status = Status.ONLINE

    def send_message(self, message):
        self.socket.sendall(message)

class HenStreamServer(StreamServer):

    WELCOME_MESSAGE =\
"""

              mmm,
             /::* > -Chit Chat!
    \        |::/
     Aaa..../:::\\
     \:::::::::::|
      \:::::::::/
       \:::::::/
         \:/\:/
          |_  \__
-------------------------------------
Welcome to the HEveNtful chat server!
-------------------------------------

"""

    HELP_MESSAGE =\
"""
usage:
    QUIT         to exit
    LIST         to list users
    DM @nick     to send direct messages to users
    DND          do not disturb
    AWAY         let others know you are away
    ONLINE       let others know when you are back online again
    HELP         show this text
"""

    def __init__(self, listener, handle=None, backlog=None, spawn='default', **ssl_args):
        super(HenStreamServer, self).__init__(listener, handle, backlog, spawn, **ssl_args)
        self.registered_users = {"magnus":"qwerty", "bobby":"12345", "svea":"frog"}
        self.clients = {} # identified by address

    def read_input(self, socket):
        fileobj = socket.makefile()

        while True:
            line = fileobj.readline()
            if not line:
                print "client disconnected"
                break

            return line.strip()

    def quit_command(self, client):
        print client.nick, "quit"
        del self.clients[client.address]
        self.multicast(client.nick + " quit\n")

    def dm_command(self, client, line):
        recipients, message = self.parse_direct_message(line)
        if recipients and message:
            self.send_direct_message(client, recipients, message)

    def parse_direct_message(self, line):
        occurences =  [m.start() for m in re.finditer('@', line)]
        recipients = []
        for e in occurences:
            recipients.append(line[e + 1:line.find(" ", e)].strip())
        print "recipients", recipients
        if e and len(occurences) > 0:
            return recipients, line[e + len(recipients[-1]) + 2:]

    def send_direct_message(self, from_client, recipients, message):
        for k, client in self.clients.items():
            if client.nick in recipients:
                if client.status == Status.DND:
                    from_client.send_message(client.nick + " wishes not to be disturb")
                elif client.status == Status.AWAY:
                    from_client.send_message(client.nick + " is away from keyboard")
                client.send_message("<" + from_client.nick + " whispers>" + message)

    def list_command(self, client):
        message = self.get_list_message()
        client.send_message(message)

    def get_list_message(self):
        list = []
        number_of_clients = len(self.clients)
        for k, c in self.clients.items():
            list.append(c.nick + "\t" + c.status)
        message = "\n".join(list)
        return str(number_of_clients) + " user" + ("s" if number_of_clients > 1 else "") +  " online\n" + message + "\n"

    def help_command(self, client):
        client.send_message("\n" + HenStreamServer.HELP_MESSAGE)

    def away_command(self, client):
        client.status = Status.AWAY
        self.multicast(client.nick + " is away\n")

    def dnd_command(self, client):
        client.status = Status.DND
        self.multicast(client.nick + " wishes not to be disturb\n")

    def online_command(self, client):
        client.status = Status.ONLINE
        self.multicast(client.nick + " is online\n")

    def say_command(self, client, message):
        if message and len(message.strip()) > 0:
            self.multicast(client.nick + " -" + message + "\n", [client])

    def login_client(self, socket, address):
        socket.sendall("login:")
        nick = self.read_input(socket)

        socket.sendall("password:")
        password = self.read_input(socket)

        if nick in self.registered_users and self.registered_users[nick] == password:

            for k, c in self.clients.items():
                if c.nick == nick:
                    self.logout_client(c)
                    break

            client = Client(socket, nick, address)
            self.clients[address] = client
            client.send_message("\n" + "Welcome " + nick + "!\nType HELP for help.\n")
            self.multicast(nick + " connected\n", [client])
            return client
        else:
            socket.sendall("Sorry, try again!")

    def logout_client(self, client):
        client.send_message("\nYou have been suspended because your account is used somewhere else.\n")
        del self.clients[client.address]

    def is_loggedin(self, address):
        return address in self.clients

    def multicast(self, message, exclude = []):
        receivers = []
        for k, client in self.clients.items():
            if not client in exclude:
                receivers.append(gevent.spawn(client.send_message, message))

        gevent.joinall(receivers)

    def handle(self, socket, address):
        print ('New connection from %s:%s' % address)
        socket.sendall(HenStreamServer.WELCOME_MESSAGE)

        if not self.is_loggedin(address):
            if not self.login_client(socket, address):
                return

        client = self.clients[address]

        fileobj = socket.makefile()

        while True:
            line = fileobj.readline()
            print "Received", line, "from", client.nick

            if not line or line.strip().lower() == 'quit':
                self.quit_command(client)
                break

            if line.startswith("DM"):
                self.dm_command(client, line)
            elif line.startswith("LIST"):
                self.list_command(client)
            elif line.startswith("HELP"):
                self.help_command(client)
            elif line.startswith(Status.AWAY):
                self.away_command(client)
            elif line.startswith(Status.DND):
                self.dnd_command(client)
            elif line.startswith(Status.ONLINE):
                self.online_command(client)
            else:
                self.say_command(client, line)

if __name__ == '__main__':
    try:
        PORT = 6000
        if len(sys.argv) > 1:
            PORT = int(sys.argv[1])

        server = HenStreamServer(('0.0.0.0', PORT))
        print ('Starting server on port', PORT)
        server.serve_forever()
    except ValueError:
        print "usage: python server.py [port]"

    except KeyboardInterrupt:
        print "^C received, shutting down server"

