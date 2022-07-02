"""CD Chat client program"""
import logging
import sys
import selectors
import socket
import fcntl
import os
import json

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)
# set sys.stdin non-blocking
#orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
#fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)


class Client:

    def __init__(self, name: str = "Foo"):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.end = 0                                        # variável para saber se devemos terminar o loop ou não
        self.channel = None                                 # variavel para guardar o channel
        self.user = name                                    # inicializacao do username
        self.selector = selectors.DefaultSelector()

    def connect(self):
        self.sock.connect(('', 8000))
        self.sock.setblocking(False)
        self.selector.register(self.sock, selectors.EVENT_READ, self.read)
        message = CDProto.register(self.user)               # RegisterMessage do user que fez connect
        CDProto.send_msg(self.sock, message)                # enviar a Message para o server

    def read(self, soc, mask):
        data = CDProto.recv_msg(self.sock)                  # receber a Message do server decoded
        logging.debug("Received: %s", data.json)            # log
        if "channel" in data.json:
            channel = data.json["channel"]
        else:
            channel = "geral"

        print('\n> recieved: {}\n< channel: {} >\n'.format(data.json["message"], channel))        # print da mensagem recebida

    def write_stdin(self, stdin, mask):
        msg = stdin.read()                                  # ler do input
        if msg.__contains__("exit"):                        # se for "exit" entao temos de terminar 
            print("exiting...")
            self.sock.close()                               # close da socket
            self.selector.unregister(self.sock)                  # unregister da socket no selector
            self.end = 1                                    # variavel a 1 para sabermos que temos de terminar o loop
            return
        if msg.__contains__("/join"):                       # se for "/join ***" entao temos de enviar JoinMessage com o channel
            msg_split = msg.split()                         # dividir a string pelos espaços
            if len(msg_split) != 2:                         # se nao tiver len() = 2 entao é pq nao deu um channel ou o channel tem espaços -> mau channel
                print("Channel Error")
                return
            self.channel = msg_split[1]                     # guardar channel
            message = CDProto.join(self.channel)            # criar JoinMessage object
        else:                                               # se nao for "exit" nem "join", como register so aparece no inicio, entao é do tipo TextMessage
            message = CDProto.message(msg.strip("\n"), self.channel)    # criar TextMessage object

        CDProto.send_msg(self.sock, message)                # enviar Message


    def loop(self):
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK) 
        self.selector.register(sys.stdin, selectors.EVENT_READ, self.write_stdin)
        sys.stdout.write('Welcome to the chat! Type anything: \n')
        sys.stdout.flush()                                  # 5 linhas para input with non_blocking
        while True:                                         # loop
            if self.end == 1:                               # se for 1, então tivemos mensagem "exit" por isso terminamos
                break
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
