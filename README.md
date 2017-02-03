# InternetRelayChat


Simple Internet Relay Chat

Introduction
This is a command line application and has two basic modules: the chatServer (chatServer.py) and chatClient (chatClient.py). An additional file chatChannel.py is a helper that contains the definition of a class chatChannel to realize a chat room.

Platform
This application has been implemented for linux and have been tested on cs.pdx.edu machine using SSH client.

Launching
The application has to be started by starting the server and then any number of clients.
The server can be started by the command: 
$python chatServer.py <server nickname>
The clients are started by the command:
$python chatClient.py CONN <nickname> localhost 4134
4134 is the port number the server is bound to.


Other Commands:
The usage of other commands are as dictated by the RFC document.

 
