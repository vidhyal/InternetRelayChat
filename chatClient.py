# chat_client.py

import sys
import socket
import select

class ChatClient:
    #this function creates a client socket and connects it to a server. It also sends a request to the server for setting the client's nick.
    # It prepares the client so that it could start listening once the run function is called.
    def __init__(self,nick,host,port):
        self.clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientsock.settimeout(2)
        self.nick = nick
        try:
            self.clientsock.connect((host,port))
            self.clientsock.send("NICK " +nick+"\n")
        except:
            print('Unable to connect')
            sys.exit
        print('Connected to remote host. You can start sending messages')
        self.socket_list = [sys.stdin, self.clientsock]

    # this command runs forever until the server exits. It gets all the sockets which are ready to be read into the read_list using the select functionality.
    # if the socket in read_list is the client itself, it recieves messages from the server and prints it.
    # if there is some request from command prompt, it reads it and sends it to server for processing. 
    def run(self):
        (read_list, write_list, error_list) = select.select (self.socket_list, [],[])
        for sock in read_list:
            if sock == self.clientsock:
                data = sock.recv(4096)
                if not data:
                    print('Disconnected from server\n')
                    sys.exit()
                else:
                    sys.stdout.write(data)
                    print ('')
            else:
                msg = sys.stdin.readline()
                self.clientsock.send(msg)
                
    # the client kills itself with this function
    def exit(self):
        sys.exit(chat_client())

# The client is created according to the 'usage' specified
if(len(sys.argv) < 5) :
    print 'Usage : python chat_client.py CONN nick hostname port'
    sys.exit()
command = sys.argv[1]
nick = sys.argv[2]
host = sys.argv[3]
port = int(sys.argv[4])

# while the client exists, it always runs and listens to the socket.
if command == "CONN":

    myclient = ChatClient(nick, host, port)
    while True:
        myclient.run()

     

    
