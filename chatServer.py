import socket
import select
import sys
from chatChannel import *

channellist=[]
userChanMap =[]
class ChatServer:
    #this function creates a server socket and binds it to a port. It prepares the server so that it could start listening once the run function is called.
    def __init__( self, nick, port):
        self.port = port;
        self.nick = nick;
        self.servsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.servsock.bind(("", port))
        self.servsock.listen(5)

        self.descriptors = [self.servsock, sys.stdin]
        self.nicklist = []
        print ('ChatServer started on port %s with nick %s' %(port,self.nick))

    
    # this command runs forever until the server exits. It gets all the sockets which are ready to be read into the read_list using the select functionality
    # if the socket is the server itself, it needs to accept a new connection from a client. If the socket is the standard input, that is the command prompt itself, it reads the message for either disconnecting a client or shutting itself down.
    # if the socket in read_list is a client, it observes the first word of the message and caaries out a function accordingly.
    def run(self):
        (read_list, write_list, error_list) = select.select (self.descriptors, [],[])
        for sock in read_list:
            if sock == self.servsock:
                self.accept_new_connection()
            elif sock == sys.stdin:
                msg = sys.stdin.readline()
                comm = (msg.split(" ")[0]).split("\n")[0]
                if comm == 'SQUIT':
                    self.exit(msg)
                elif comm == 'DISCONN':
                    self.disClient(msg)
                else:
                    print('invalid command')
            else:
                str = sock.recv(4096)
                if str == '':
                    self.disconn(sock)
                else:
                    comm = (str.split(" ")[0]).split("\n")[0]
                    if comm =='NICK':
                        self.nickname(str, sock)
                    elif comm == 'QUIT':
                        self.quitmsg(str, sock)
                    elif comm == 'JOIN':
                        self.joinchann(str,sock)
                    elif comm == 'LEAVE':
                        self.leavechan(str,sock);
                    elif comm == 'TOPIC':
                        self.changetop(str,sock)
                    elif comm =='LIST':
                        self.listchan(str,sock)
                    elif comm == 'LISTMEM':
                        self.listmem(str,sock)
                    elif comm == 'PRIVMSG':
                        self.privmsg(str,sock)
                    elif comm == 'GRPMSG':
                        self.grpmsg(str,sock)
                    else:
                        sock.send("Please enter a valid command") #ERR_NOSUCHCOMMAND

    def nocomm(self, str,sock):
        sock.send("Please enter a valid command") #ERR_NOSUCHCOMMAND
                    

    # This function broadcasts any message from a socket to all other sockets in the system.
    def broadcast_string(self, str, omit_sock):
        for sock in self.descriptors:
            if sock!=self.servsock and sock != omit_sock:
                sock.send(str)
        
    # the server accepts new connections (from clients) with the help of this function
    def accept_new_connection(self):
        newsock, (new_host, new_port) = self.servsock.accept()
        self.descriptors.append(newsock)
        newsock.send (' you are connected to chatServer on port %s\r\n' %self.port) #RPL_CONNECTED
        str = 'Client joined %s:%s' % (new_host, new_port)
        print(str)
        
    # this function checks few conditions on the nickname mentioned by the client and if it is valid and available, assigns it to the client. The client may anytime change the nickname.
    def nickname(self, str, sock):
        nick =(str.split(" ")[1]).split("\n")[0]
        if nick[0].isalpha()and len(nick)<=10 and len(nick)>0:
            host,port = sock.getpeername()
            c = 0
            sockexists =0
            for n in self.nicklist:
                if n[1] == sock:
                    sockexists =1
            for n in self.nicklist:
                if n[0] == nick:
                    c=1
            if sockexists ==1:
                for n in self.nicklist:
                    if n[0] == nick:
                        if n[1] != sock:
                           sock.send('Nickname is already in use') #ERR_NICKCOLLISION
                           c=1
                if c==0:
                    for n  in self.nicklist:
                        if n[1] == sock:
                            self.nicklist.remove(n)
                            t = nick, sock
                            self.nicklist.append(t)
            else:
                if c==0:
                    t = nick,sock
                    self.nicklist.append(t)
                else:
                    sock.send('Nickname is already in use') #ERR_NICKCOLLISION
                    self.disconn (sock)
        else:
            sock.send('First character of nick name should be a letter and length of nickname should be less than 10')#ERR_NICKISSUE 

    # this function is called when a client QUITs. The message needs to be propagated to all the clients with whom this client shares a channel
    def quitmsg(self, str, sock):
        if len(str.split(" "))<2:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            
            for n in self.nicklist:
                if sock == n[1]:
                    nick = n[0]
                    break
            self.disconn(sock)
            self.removeNick(sock)
            print ('Client %s leaving: %s' % (nick, str.split(" ")[1]))
            
    #this function checks existence of a channel and if does, adds the user to that channel if there is vacancy and notifies the other clients on the channel. If the channel doesn't exist, then it creates a channel by that name and user joins it.
    def joinchann (self, str, sock):
        if len(str.split(" "))<2:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            name = (str.split(" ")[1]).split("\n")[0]
            if name[0] != '#':
                sock.send('Channel name should begin with #') #ERR_CHANNELISSUE
            else:
                try:
                    key = (str.split(" ")[2]).split("\n")[0]
                except:
                    key =None
                try:
                    topic = (str.split(" ")[3]).split("\n")[0]
                except:
                    topic = None
                channelexists =0
                userinchannel=0
                channel = self.getchannel(name)
                nick = self.getNick(sock)
                if channel is None:
                    newchannel = chatChannel(name, key,topic)
                    channellist.append(newchannel)
                    newchannel.addUser(sock,nick)
                    self.addToUser(sock, newchannel)
                    print ('Client joined newly created channel %s' % name)
                    
                else:
                    if len(channel.userlist)<50:
                        key2 = channel.key
                        if key2 == key:
                            sock2 = channel.getUser(sock)
                            if sock2 is None:
                                channel.addUser(sock,nick)
                                self.addToUser(sock,channel)
                                print ('Client joined channel %s' % name)
                            else:
                                sock.send('You are already on channel %s' %name) #ERR_ALREADYONCHANNEL
                        else:
                            sock.send('Invalid key: Cannot join channel %s ' % name)  #ERR_BADCHANNELKEY
                    else:
                        sock.send(' Maximum number of users in channel %s, try again later' %name) #ERR_MAXUSERS
                
    #this function checks conditions and if user is on the channel mentioned, calls the function to removeUser and notify all clients on the channel
    def leavechan(self, str, sock):
        if len(str.split(" "))<2:
            sock.send('need more params') #ERR_NEEDMOREPARAMS
        else:
            name = (str.split(" ")[1]).split("\n")[0]
            channel = self.getchannel(name)
            if channel is None:
                sock.send('There is no such channel') #ERR_NOSUCHCHANNEL
            else:
                sockU = self.getUser(channel, sock)
                if sockU is None:
                    sock.send (' You are not on channel %s' %name) #ERR_NOTONCHANNEL
                else:
                    self.removeUser(channel, sock)
                    
    #this function sets the topic of the channel specified
    def changetop(self, str, sock):
        length = len(str.split(" "))
        if len(str.split(" "))<2:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            name = (str.split(" ")[1]).split("\n")[0]
            channel = self.getchannel(name)
            if channel is None:
                sock.send('There is no such channel') #ERR_NOSUCHCHANNEL
            else:
                userinchannel = channel.getUser(sock)
                if not userinchannel is None:
                    topic = ""
                    try:
                        for i in range (2, length ):
                            topic  = topic +(str.split(" ")[i]).split("\n")[0] + " "
                    except:
                        topic = None
                    channel.setTopic(topic)
                    channel.sendMessage((' The topic of channel %s has been set to %s' % (name, topic)), None)
                else:
                    sock.send(' You are not on channel %s' %name) #ERR_NOTONCHANNEL

    #this function sends to the user the list of channels available when no particular channel is mentioned and the topic of the channel if a channel is specified
    def listchan(self,str,sock):
        length = len(str.split())
        if length ==1:  
            namelist = ''
            numberofchan =0
            for n in channellist:
                namelist=namelist + n.name + "\n"
                numberofchan = numberofchan +1
            if numberofchan ==0:
                sock.send('No channels yet') #ERR_NOCHANNELS
            else:
                namelist ='List Start\n'+ namelist+ 'List End\n'  #RPL_LISTSTART, RPL_LIST, RPL_LISTEND
                sock.send(namelist)
        else:
            name = (str.split(" ")[1]).split("\n")[0]
            channel = self.getchannel(name)
            if channel is None:
                sock.send('There is no such channel') #ERR_NOSUCHCHANNEL
            else:
                topic =channel.getTopic()
                if topic is None:
                    sock.send('No topic yet on channel %s' %name) #RPL_NOTOPIC
                else:
                    sock.send (topic)
            
    # this function checks if the requesting socket is on the channel and if yes, gives the socket a list of nick names on the channel.
    def listmem(self,str,sock):
        length = len(str.split(" "))
        if length <2:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            name = (str.split(" ")[1]).split("\n")[0]
	    
            channel = self.getchannel(name)
            if channel is None:
                sock.send('There is no such channel') #ERR_NOSUCHCHANNEL
            else:
                onchannel = self.getUser(channel, sock)
                if onchannel is None:
                    sock.send(' You are not on channel %s' %name) #ERR_NOTONCHANNEL
                else:
                    nicklist =''
                    for i in channel.userlist:
                        nicklist = nicklist + self.getNick(i) + "\n"
                    nicklist = 'List Start\n'+ nicklist+ 'List End\n'  #RPL_LISTSTART, RPL_NAMES, RPL_LISTEND
                    sock.send(nicklist)

    #this function forwards a private message to the user specified by the nick
    def privmsg(self, str, sock):
        length = len(str.split(" "))
        if length <3:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            nick = self.getNick(sock)
            nickrecv = (str.split(" ")[1]).split("\n")[0]
	    if nickrecv == nick:
                sock.send('Hey! You can\'t send yourself a message') #ERR_SELFMSG
            else:
                sockrecv = self.getSock(nickrecv)
                if sockrecv is None:
                    sock.send ('%s: No such nick' %nick ) #ERR_NOSUCHNICK
                else:
                    msg = ""
                    try:
                        for i in range (2, length ):
                            msg  = msg + (str.split(" ")[i]).split("\n")[0]+ " "
                    except:
                        msg =None
                    if msg is None:
                        sock.send('No text to send') #ERR_NOTEXTTOSEND
                    else:
                        msg = '[' + nick + '] ' +msg
                        sockrecv.send(msg)
                     
    #this function checks for users on a particular channel and sends a message to all the clients in the channel except the one sending the message
    def grpmsg (self, str, sock):
        length = len(str.split(" "))
        if length <3:
            sock.send('Need more parameters') #ERR_NEEDMOREPARAMS
        else:
            nick = self.getNick(sock)
            channame = (str.split(" ")[1]).split("\n")[0]
            channel = self.getchannel(channame)
            if channel is None:
                sock.send('There is no such channel') #ERR_NOSUCHCHANNEL
            else:
                onchannel = self.getUser(channel, sock)
                if onchannel is None:
                    sock.send(' You are not on channel %s' %channame) #ERR_NOTONCHANNEL
                else:
                    msg = ""
                    try:
                        for i in range (2, length ):
                            msg  = msg + (str.split(" ")[i]).split("\n")[0]+ " "
                    except:
                        msg =None
                    if msg is None:
                        sock.send('No text to send') #ERR_NOTEXTTOSEND
                    else:
                        msg = '[' + nick + '@' + channame +'] ' +msg
                        for sockrecv in channel.userlist:
                           if sock != sockrecv:
                               sockrecv.send (msg)
                    
    #this functions returns the nick name corresponding to the socket given
    def getNick(self, sock):
        for n in self.nicklist:
            if n[1]==sock:
               return n[0]
            
    #this function returns the socket corresponding to the nick name specified
    def getSock(self, nick):
        for n in self.nicklist:
            if n[0]==nick:
               return n[1]

    #this function returns the channel object that has the name mentioned
    def getchannel(self,name):
        for n in channellist:
            if n.name == name:
                return n

    #this function searches the list of users of a channel and returns the socket in the list        
    def getUser (self,channel, sock):
        for n in channel.userlist:
            if n == sock:
                return n
    #this function removes a socket from a channel's list and also the channel from the socket's channel list
    def removeUser (self,channel,sock):
        nick = self.getNick(sock)
        channel.removeUser(sock,nick)
        self.removeFromUser(sock, channel)
        

    def removeNick(self, sock):
        for n in self.nicklist:
            if n[1] == sock:
                self.nicklist.remove(n)

    def disconn (self, sock):
        host, port = sock.getpeername()
        for mapp in userChanMap:
            if mapp[0] == sock:
                while mapp[1]:
                    for chan in mapp[1]:
                        self.removeUser(chan,sock)
                userChanMap.remove(mapp)
        for n in self.nicklist:
            if n[1] == sock:
                self.nicklist.remove(n)
        sock.shutdown(socket.SHUT_RDWR)
        sock.close
        self.descriptors.remove(sock)
        #removeNick(sock)
        str = 'Client left %s:%s\n' % (host, port)
        print (str)

    def addToUser (self, sock, channel):
        userhaschans =0
        for mapp in userChanMap:
            if mapp[0] == sock:
                mapp[1].append(channel)
                userhaschans =1
                break
        if userhaschans==0:
            channelL = [channel]
            userChanMap.append((sock, channelL))
        
            
    def removeFromUser(self, sock, channel):
        for mapp in userChanMap:
            if mapp[0]== sock:
                for chan in mapp[1]:
                    if chan == channel:
                        mapp[1].remove(chan)
        

    def disClient(self, str):
        if len(str.split(" ")) >=2:
            nick = (str.split(" ")[1]).split("\n")[0]
            sock = self.getSock(nick)
            if not sock is None:
                sock.send('server is disconnecting you') #RPL_DISCONNECTED
                self.disconn(sock)


    def exit(self, str):
        for n in self.nicklist:
            n[1].send ('server is quitting: %s'%str)  #RPL_SQUIT
        sys.exit()

if(len(sys.argv) < 2) :
    print ('Usage : python chatServer.py nick')
    sys.exit()
  
nick = sys.argv[1]
port = 4134
myServer = ChatServer (nick, port)
while True:
    myServer.run()
