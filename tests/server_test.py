import unittest
from hen.server import HenStreamServer, Client, Status


class MakeFileStub():

    def __init__(self, line):
        self.line = line

    def readline(self):
        return self.line

class SocketStub():

    def __init__(self, lines = [""]):
        self.lines = lines
        self.line_counter = -1
        self.received_messages = []

    def makefile(self):
        self.line_counter += 1
        if self.line_counter + 1 >= len(self.lines):
            self.line_counter = -1
        return MakeFileStub(self.lines[self.line_counter])

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

        self.address_a = ("localhost", 50000)
        self.address_b = ("localhost", 50001)
        self.address_c = ("localhost", 50002)

        self.client_a = Client(self.socket_a, "adam", self.address_a)
        self.client_b = Client(self.socket_b, "ben", self.address_b)
        self.client_c = Client(self.socket_c, "clemens", self.address_c)

        self.server.clients[self.client_a.address] = self.client_a
        self.server.clients[self.client_b.address] = self.client_b
        self.server.clients[self.client_c.address] = self.client_c

    def test_read_input_should_return_client_input(self):
        # given
        line = "a line of text"
        socket = SocketStub([line])

        # then
        self.assertEqual(line, self.server.read_input(socket))

    def test_read_input_should_strip_output(self):
        # given
        line = "a line of text"
        socket = SocketStub(["\n"+ line + "\t\n"])

        # then
        self.assertEqual(line, self.server.read_input(socket))

    def test_read_input_should_return_none_if_client_is_assumed_disconnected(self):
        # given a socket that will return None
        socket = SocketStub([None])

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

    def test_dm_command(self):
        # when
        self.server.dm_command(self.client_a, "DM @clemens Hello Clemens")

        #then
        expected_message = "\n<adam whispers>Hello Clemens\n"
        self.assertEqual(expected_message, self.client_c.socket.received_messages[0])


    def test_get_list_message(self):
        # given clients have different statuses
        self.client_b.status = Status.AWAY
        self.client_c.status = Status.DND

        # when
        message = self.server.get_list_message()

        # then current statuses should be displayed
        expected_message = \
"""3 users online
ben	AWAY
clemens	DND
adam	ONLINE"""

        self.assertEqual(expected_message, message)

    def test_list_command(self):
        # when
        self.server.list_command(self.client_a)

        # then
        expected_message = "\n3 users online\nben\tONLINE\nclemens\tONLINE\nadam\tONLINE\n"
        self.assertEqual(expected_message, self.client_a.socket.received_messages[0])



    def test_help_command(self):
        # when
        self.server.help_command(self.client_a)

        # then
        self.assertEqual(HenStreamServer.HELP_MESSAGE.strip(), self.client_a.socket.received_messages[0].strip())

    def test_away_command(self):
        # when a client Adam sets status "AWAY"
        self.server.away_command(self.client_a)

        # then all clients receive a "Adam is away" message
        expected_message = "\nadam is away\n"
        self.assertEqual(expected_message, self.client_a.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_b.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_c.socket.received_messages[0])

    def test_dnd_command(self):
        # similar when a client Adam sets status "DND"
        self.server.dnd_command(self.client_a)

        # then all clients receive a "Adam wishes not be disturb" message
        expected_message = "\nadam wishes not be disturb\n"
        self.assertEqual(expected_message, self.client_a.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_b.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_c.socket.received_messages[0])

    def test_online_command(self):
        # similar when a client Adam sets status "ONLINE"
        self.server.online_command(self.client_a)

        # then all clients receive a "Adam is online" message
        expected_message = "\nadam is online\n"
        self.assertEqual(expected_message, self.client_a.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_b.socket.received_messages[0])
        self.assertEqual(expected_message, self.client_c.socket.received_messages[0])

    def test_say_command(self):
        # when adam says "Hi Guys!"
        message = "Hi guys!"
        self.server.say_command(self.client_a, message)

        # then ben and clemens receive "adam -Hi guys!"
        expected_message = "adam -" + message
        self.assertEqual(expected_message, self.client_b.socket.received_messages[0].strip())
        self.assertEqual(expected_message, self.client_c.socket.received_messages[0].strip())

        # ... but not adam
        self.assertEqual(0, len(self.client_a.socket.received_messages))

    def test_is_loggedin(self):
        # given
        socket = SocketStub(["magnus", "qwerty"])
        address = ("localhost", 50042)

        self.assertFalse(self.server.is_loggedin(address))

        # when
        self.assertTrue(self.server.login_client(socket, address))

        # then
        self.assertTrue(self.server.is_loggedin(address))

    def test_login_client_with_a_non_registered_user(self):
        # given
        socket = SocketStub(["non_registered_user", "qwerty"])
        address = ("localhost", 50042)

        # then
        self.assertFalse(self.server.login_client(socket, address))
        self.assertFalse(self.server.is_loggedin(address))

    def test_handle_quit(self):
        # given
        socket = SocketStub(["magnus", "qwerty", "quit"])
        address = ("localhost", 50042)

        # when
        self.server.handle(socket, address)


    def test_handle_wrong_password(self):
        # given
        socket = SocketStub(["magnus", "foobar", "quit"])
        address = ("localhost", 50042)

        # when
        self.server.handle(socket, address)


if __name__ == '__main__':
    unittest.main()





