"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command):                    # construtor para o dicionario que depois vai ser json
        if command == "register":
            self.json = {"command": command, "user": self.user}
        elif command == "join":
            self.json = {"command": command, "channel": self.channel}
        elif command == "message":
            self.json = {"command": command, "message": self.message, "ts": self.ts, "channel": self.channel}
            if self.json["channel"] == None:
                self.json.pop("channel")                # se o channel for None entao nao aparece no json
    
    def __str__(self):                                  # json para string
         return json.dumps(self.json)


class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, channel):
        self.channel = channel
        super().__init__("join")                        # tipo JoinMessage


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, user):
        self.user = user
        super().__init__("register")                    # tipo RegisterMessage


class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, message, channel):
        self.channel = channel
        self.ts = int(datetime.now().timestamp())
        self.message = message
        super().__init__("message")                     # tipo TextMessage


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        register = RegisterMessage(username)
        return register

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        join = JoinMessage(channel)
        return join

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        messages = TextMessage(message, channel)
        return messages

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        data = json.dumps(msg.json).encode('utf-8')                 # codificar a mensagem depois de transformar em json
        header = len(data).to_bytes(2, "big")                       # header codificado em 2 bytes, big endian
        connection.sendall(header+data)                             # enviar o header + data pela socket

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        header = int.from_bytes(connection.recv(2), "big")          # descodificar os 2 bytes, big endian para o header
        message_encoded = connection.recv(header)                   # ler o numero de bytes a que o header corresponde
        message_decoded = message_encoded.decode("utf-8")           # descodificar a data

        if len(message_decoded) == 0:                               # se nao existir data entao faz return
            return False
        try:
            message_recv = json.loads(message_decoded)              # se nao conseguir fazer load do json entao raise CDProtoBadFormat, se sim entao guarda na variavel
        except:
            raise CDProtoBadFormat(message_encoded)

        if message_recv["command"] == "join":                       # verificar de que tipo é e criar o object desse tipo com as caracteristicas na data
            object = CDProto.join(message_recv["channel"])
        elif message_recv["command"] == "register":
            object = CDProto.register(message_recv["user"])
        elif message_recv["command"] == "message":
            if "channel" in message_recv:                           # se o channel estiver na data entao guardamos o channel
                channel = message_recv["channel"]
            else:                                                   # se nao esta entao o chnnael = None
                channel = None
            object = CDProto.message(message_recv["message"], channel)
            object.json["ts"] = message_recv["ts"]                  # ts modificado quando criado o novo object, por isso guardamos o antigo
        return object


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes = None):
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
