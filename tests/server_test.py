import unittest
from hen.server import HenStreamServer, Client, Status


class MakeFileStub():

    def __init__(self, line):
        self.line = line

    def readline(self):
        return self.line

class SocketStub():

    def __init__(self, line = ""):
        self.line = line
        self.received_messages = []

    def makefile(self):
        return MakeFileStub(self.line)

    def sendall(self, message):
        self.received_messages.append(message)



class ServerTest(unittest.TestCase):

    def setUp(self):
        HOST = "0.0.0.0"
        PORT = 7777

        self.server = HenStreamServer((HOST, PORT))
        self.socket_a = SocketStub()
        self.socket_b = SocketStub()
        self.socket_c = SocketStub()

        self.client_a = Client(self.socket_a, "Adam", ("localhost", 50000))
        self.client_b = Client(self.socket_b, "Ben", ("localhost", 50001))
        self.client_c = Client(self.socket_c, "Clemens", ("localhost", 50002))

        self.server.clients[self.client_a.address] = self.client_a
        self.server.clients[self.client_b.address] = self.client_b
        self.server.clients[self.client_c.address] = self.client_c


    def test_read_input_should_return_client_input(self):
        # given
        line = "a line of text"
        socket = SocketStub(line)

        # then
        self.assertEqual(line, self.server.read_input(socket))

    def test_read_input_should_strip_output(self):
        # given
        line = "a line of text"
        socket = SocketStub("\n"+ line + "\t\n")

        # then
        self.assertEqual(line, self.server.read_input(socket))

    def test_read_input_should_return_none_if_client_is_assumed_disconnected(self):
        # given a socket that will return None
        socket = SocketStub(None)

        # then
        self.assertIsNone(self.server.read_input(socket))

    def test_quit_command_should_remove_client(self):
        # given
        socket = SocketStub()
        nick = "Nick"
        address = ("localhost", 50000)
        client = Client(socket, nick, address)
        self.server.clients[client.address] = client

        # when
        self.server.quit_command(client)

        # then
        self.assertFalse(client in self.server.clients)

    def test_parse_direct_message(self):
        # given Adam wants to send a direct message to Ben
        from_client = self.client_a
        direct_message = "DM @ben Hello Ben!"

        # when
        recipients, message = self.server.parse_direct_message(from_client, direct_message)

        # then
        self.assertEqual(['ben'], recipients)
        self.assertEqual("Hello Ben!", message)

    def test_get_list_message(self):
        # given
        self.client_b.status = Status.AWAY
        self.client_c.status = Status.DND

        # when
        message = self.server.get_list_message()

        # then
        expected_message = \
"""3 users online
Ben	AWAY
Clemens	DND
Adam	ONLINE"""

        self.assertEqual(expected_message, message)




if __name__ == '__main__':
    unittest.main()



