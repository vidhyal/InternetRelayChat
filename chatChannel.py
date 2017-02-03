import socket
import select
import sys

# this is a structure to emulate chat rooms. the chatChannel can be viewed as a chat room taht has a name, topic and users in the room. It also has few methods in order to access its fields.
class chatChannel:
    #create a chat channel when this function is called ( the server calls this functon while creating a new room).
    def __init__ (self, name, key,topic):
        self.name = name
        if key is None:
            self.key = None
        else:
            self.key = key
        self.userlist=[]
        if topic is None:
            self.topic = None
        else:
            self.topic = topic

    # this function adds the given socket to the list of users of the chat channel and notoifies its other users
    def addUser (self, sock,nick):
        self.userlist.append(sock)
        self.sendMessage('%s joined the channel %s' %(nick,self.name), sock)

    # this function removes the specified user from the chat channel and notifies the other users of the event
    def removeUser(self, sock,nick):
        sock2 = self.getUser(sock)
        self.userlist.remove(sock2)
        self.sendMessage('%s left the channel %s' %(nick,self.name), sock)
       
    # this function sends teh given message to all sockets on the channel except for the one mentioned.
    def sendMessage (self,str,sock):
        for n in self.userlist:
            if n != sock:
                n.send(str)

    # this function returns teh topic of the chat channel
    def getTopic(self):
        return self.topic

    # this function sets the channel's topic
    def setTopic(self,topic):
        self.topic = topic

   # this function returns the socket if it is in the channel's list, else returns none.
    def getUser(self, sock):
        for n in self.userlist:
            if n == sock:
                return sock
