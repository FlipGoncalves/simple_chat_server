"""CD Chat server program."""
import logging
import selectors
import socket
import json

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    connecs = {}                                                        # inicializacao de um dicionario de auxilio

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()
        self.sock.bind(('', 8000))
        self.sock.listen(100)
        # self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        print("Starting server...")

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        # conn.setblocking(False)
        self.connecs[conn] = []                                         # inicializacao da key correspondente à socket no dicionario
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        data_message = CDProto.recv_msg(conn)                                   # receber a Message do client decoded
        if not data_message:                                                    # se nao existir data naquela socket, entao a socket foi terminada
            print('-----Closing Connection to: {}-----'.format(self.connecs[conn][0]))      
            self.sel.unregister(conn)                                        # unregister da socket no selector
            self.connecs.pop(conn)                                      # eliminar a key e os values correspondentes da key que é a socket
            conn.close()                                                # fechar a socket
            return
        logging.debug("Received: %s", data_message)                             # log
        data = data_message.json
        if data["command"] == "join":                                   # dependendo do tipo
            self.connecs[conn][1].append(data["channel"])               # guardamos no index 1 da lista (value da socket no dicionario) o channel do client
            print('{} joined {}'.format(self.connecs[conn][0], data["channel"]))
        elif data["command"] == "message":
            self.broadcast(data_message, self.connecs[conn][1][-1])                 # fazemos broadcast da data para os clients todos
            print('{} sent a message to {}'.format(self.connecs[conn][0], self.connecs[conn][1][-1]))
        elif data["command"] == "register":
            self.connecs[conn].append(data["user"])                     # como Register Message é a primeira a ser enviada, guardmos na lista no index
            self.connecs[conn].append(["geral"])                                                                                      # 0 o username e no index 1 o channel
            print("User Connected: {}".format(data["user"]))

    def loop(self):
        while True:                                                     # loop
            events = self.sel.select()   
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def broadcast(self, message, channel):                              # envia para os clients todos
        for client in self.connecs:                                     # para cada socket
            if str(channel) in self.connecs[client][1]:                 # se o channel for igual ao da data a ser enviada enato enviada para essa socket
                CDProto.send_msg(client, message)                       # send data