#!/usr/bin/python
""" cherrypy_example.py

    COMPSYS302 - Software Design
    Author: Andrew Chen (andrew.chen@auckland.ac.nz)
    Last Edited: 19/02/2018

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
listen_ip = "0.0.0.0" 
listen_port = 10001
# gets user name   cherrypy.session['username']
import cherrypy
import DataBase
import hashlib
import urllib2
import json
import socket
import mimetypes
import base64
import time
import os
import datetime
from jinja2 import Environment, FileSystemLoader

from Timer import Timer


class MainApp(object):




    #CherryPy Configuration
    # move to 
    _cp_config = {'tools.encode.on': True, 
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on' : 'True',
                 }                 

    # If they try somewhere we don't know, catch it here and send them to the right place.


    def __init__(self):
        try:
            getUsers = self.serverListUsers()
            DataBase.setupDataBase(getUsers)
        except:
            pass
        finally:
            self.report = Timer(self.serverReport, 40)
            self.report.start()
            self.report.pause()
            self.hashPassword = None
            self.username = None
            self.userLogged = False
            self.sendingTo = None
            



    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    def ping(self, sender=None):
        if sender != None:
            return '0'
        else:
            return('1: Missing required field')

    # PAGES (which return HTML that can be viewed in browser)
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('/login')
        
    @cherrypy.expose
    def login(self):
        return file('loginPage.html') 

    @cherrypy.expose
    def setSendingto(self,sendTo):
        self.sendingTo = sendTo
        destination = self.loadMessageScreen()
        return destination





    @cherrypy.expose
    def loadMessageScreen(self):
        userList = self.getList()
        messagesList = DataBase.getMessages(self.username, self.sendingTo)
        for key in messagesList:
            stamp = float(key['stamp'])
            stampFloat = datetime.datetime.fromtimestamp(stamp).strftime('%d-%m-%Y %H:%M:%S')
            stampString = time.strftime(stampFloat)
            key['stamp'] = stampString
        folderLoad = FileSystemLoader('temp')
        createEnvironment = Environment(loader = folderLoad)
        getMsgPage = createEnvironment.get_template('MsgUserPage.html')
        messegePage = getMsgPage.render(userList = userList, sendingTo = self.sendingTo, msgDic = messagesList)
        return messegePage
          

    
    @cherrypy.expose    
    def MessegesScreen(self):
        userList = self.getList()
        DataBase.updateUserTable(userList)
        folderLoad = FileSystemLoader('temp')
        createEnvironment = Environment(loader = folderLoad)
        getMsgPage = createEnvironment.get_template('onlineUsers.html')
        messegePage = getMsgPage.render(userList = userList)
        return messegePage

    
    
    @cherrypy.expose
    def sendFile(self, fileSent=None):
        try:
            fileName = fileSent.filename
            fileType = fileSent.content_type.value
            encodedFile = base64.b64encode(fileSent.file.read())

            output = {"sender":self.username, "destination":self.sendingTo,"stamp":time.time(), "file": encodedFile,"filename":fileName, "content_type": fileType}
            data = json.dumps(output)
            ip = DataBase.getSenderIP(self.sendingTo)
            port = DataBase.getSenderPort(self.sendingTo)
            url = 'http://'+ ip +':' + port +'/receiveFile'
            req = urllib2.Request(url,data, {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req, timeout=5).read()
            if '0' in response:
                output = {"sender":self.username, "destination":self.sendingTo,"stamp":time.time(), "file": encodedFile,"filename":fileName, "content_type": fileType, "status":'File Sent'}
                # Add code for embeded view her
                DataBase.saveMessage(output)
            else:
                output = {"sender":self.username, "destination":self.sendingTo,"stamp":time.time(), "file": encodedFile,"filename":fileName, "content_type": fileType, "status":'File Failed Incorrect Response'}
                DataBase.saveMessage(output)
        except:
            output = {"sender":self.username, "destination":self.sendingTo,"stamp":time.time(), "file": encodedFile,"filename":fileName, "content_type": fileType, "status":'File Failed Timout'}   
            DataBase.saveMessage(output)
        return self.loadMessageScreen()







    @cherrypy.expose
    def sendMessage(self, message=None):
        # if msg not blank then send
        try:
            output = {"sender":self.username, "destination":self.sendingTo,"message":message, "stamp":time.time()}
            data = json.dumps(output)
            ip = DataBase.getSenderIP(self.sendingTo)
            port = DataBase.getSenderPort(self.sendingTo)
            url = 'http://'+ ip +':' + port +'/receiveMessage'
            req = urllib2.Request(url,data, {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req, timeout=5).read()
            if '0' in response:
                output = {"sender":self.username, "destination":self.sendingTo,"message":message, "stamp":time.time(), "status": 'Message Sent'}
                DataBase.saveMessage(output)
            else:
                output = {"sender":self.username, "destination":self.sendingTo,"message":message, "stamp":time.time(), "status": 'Message Failed Incorrect Response'}
                DataBase.saveMessage(output)
        except:
            output = {"sender":self.username, "destination":self.sendingTo,"message":message, "stamp":time.time(), "status": 'Message Failed TimeOut'}
            DataBase.saveMessage(output)
        return self.loadMessageScreen()



    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        try:
            inputData = cherrypy.request.json
            if(('sender' or 'destination' or 'message' or 'stamp') not in inputData):
                return '1: Missing compulsory Field'
            DataBase.saveMessage(inputData)
            print(inputData)
            return '0: Successfully received'
        except:
            return '1' 

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):
        try:
            inputData = cherrypy.request.json
            fileSize = len(inputData['file']) * 3 / 1024 
            if(('sender' or 'destination' or 'stamp' or 'filename' or 'file' or 'content_type') not in inputData):
                return '1: Missing compulsory Field'
            if(fileSize > 5120 * 4):
                return '1: File Size too large'
            decodedFile = base64.b64decode(inputData['file'])
            with open('static/downloads/'+inputData['filename'], 'wb') as fileSave:
                fileSave.write(decodedFile)
            contentType = mimetypes.guess_type(inputData['filename'])[0]
            html = '<a href="' + os.path.join('..','static','downloads',inputData['filename']) + '\" download>' + inputData['filename'] + '</a>'
            if 'audio/' in contentType:
                html = '<audio controls><source src="../static/downloads/'  +inputData['filename'] + '" type="' + contentType + '"></audio>'
            if 'image/' in contentType:
                html = '<img src="' + '../static/downloads/'+inputData['filename'] + '\" alt=\"' + inputData['filename'] + '\" width="320">'
            if 'video/' in contentType:
                html = '<video width="320" height="240" controls><source src="' + os.path.join('..','static','downloads',inputData['filename']) + '\" type=\"' + contentType + '\"></video>'
            loadInfo = {"sender": inputData['sender'], "destination": inputData['destination'],"message":html, "stamp": inputData['stamp'], "file": inputData['file'], "filename":inputData['filename'], "content_type":contentType }
            DataBase.saveMessage(loadInfo)
            return '0:File Receieved'
        except:
            return '1'

    @cherrypy.expose
    def home(self):
        userProfile = DataBase.getUserProfile(self.username)
        name = userProfile[1]
        pos = userProfile[3]
        dis= userProfile[4]
        picLink = userProfile[5]
        page = open('homePage.html').read().format(userName = name, userPic = picLink,userPosition = pos, userBio = dis) 
        return page


        # return file('test.html') 
    @cherrypy.expose
    def logoutScreen(self):
        return file('signOutConfirmation.html') 

    @cherrypy.expose
    def signUpScreen(self):
        return file('signUpPage.html') 
    
    @cherrypy.expose
    def EditProfileScreen(self):
        return file('editProfilePage.html') 
   
   


    @cherrypy.expose    
    def sum(self, a=0, b=0): #All inputs are strings by default
        output = int(a)+int(b)
        return str(output)

        
    # LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):
        """Check their name and password and send them either to the main page, or back to the main login screen."""
        success = self.authoriseUserLogin(username,password)
        # if its login is empty make sure it crases properly and doesnt give error
        if (success == 0):
            self.username  = username
            self.userLogged = True
            
   
            raise cherrypy.HTTPRedirect('/home')
        else:
            self.username = None
            self.userLogged = False
            raise cherrypy.HTTPRedirect('/login')

    @cherrypy.expose
    def signUp(self, FullName=None, email=None, username=None, password=None):
        checkValidCredentials = DataBase.signUpNewUser(FullName,email,username,password)
        if(checkValidCredentials == 0):
            raise cherrypy.HTTPRedirect('/login')
        else:
            raise cherrypy.HTTPRedirect('/signUpScreen')



    @cherrypy.expose
    def editProfile(self, FullName=None, position=None, description=None, profilePic=None):
        dict = {'FullName': FullName, 'position': position, 'description': description, 'profilePic': profilePic }
        DataBase.updateUserProfile(dict, self.username )
        raise cherrypy.HTTPRedirect('/home')


    @cherrypy.expose
    def signout(self,username=None, password=None):
        url = "https://cs302.pythonanywhere.com/logoff/?username=" + self.username  + "&password=" + self.hashPassword + "&enc=0"
        response = urllib2.urlopen(url).read()
        if response == "0, Logged off successfully":
            self.username  =None
            self.hashPassword =None
            self.userLogged = False
            raise cherrypy.HTTPRedirect('/login')
        else:
            self.userLogged = True
            raise cherrypy.HTTPRedirect('/home')

    @cherrypy.expose
    def shutdown(self):
        self.userLogged = False
        self.report.pause()
        cherrypy.engine.exit()
        

    
    def authoriseUserLogin(self, username, password):
        try:
            rep = self.serverReport(username, password)
            if rep== "0, User and IP logged":
                self.hashPassword = hashlib.sha256((password+username).encode('utf-8')).hexdigest()
                cherrypy.session['hashPassword'] = self.hashPassword
                self.userLogged = True
                self.username= username
                cherrypy.session['username'] = username
                cherrypy.session['hashPass'] = hashlib.sha256((password+username).encode('utf-8')).hexdigest()
                # users = self.getList()
                # print(users)
                # DataBase.updateUserTable(users)
                return 0
            else:
                return 1
        except:
            return 1


    def severListAPI(self):
        try:
            url = "https://cs302.pythonanywhere.com/listAPI"
            response = urllib2.urlopen(url).read()
            return response
        except:
            return

    def serverListUsers(self):
        try:
            url = "https://cs302.pythonanywhere.com/listUsers"
            response = urllib2.urlopen(url).read()
            return response.split(",")
            
        except:
            return []

    def serverReport(self, username=None, password=None):
        if(password == None):
            password = self.hashPassword
        if(username == None):
            username = self.username
        try:
            if (password != self.hashPassword):
                hashPassword = hashlib.sha256((password+username).encode('utf-8')).hexdigest()
            else:
                hashPassword = password
            finIP = ""
            jsonIP = json.loads(urllib2.urlopen("https://api.ipdata.co/").read())
            ip = jsonIP['ip']
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            localIP = sock.getsockname()[0]
            sock.close()
            if localIP.startswith("10.10"):
                finIP = localIP
                location = "0"
            elif localIP.startswith("172.2"): 
                finIP = localIP
                location = "1"
            else:
                finIP = ip
                location = "2"
            url = "https://cs302.pythonanywhere.com/report/?username=" + username + "&password=" + hashPassword + "&location=" + location + "&ip="+ finIP + "&port=" + str(listen_port) +"&enc=0"
            resp = urllib2.urlopen(url).read()
            if self.userLogged and resp == "0, User and IP logged":
                
                usersOnline = self.getList()
            #     # print(users)
                DataBase.updateUserTable(UsersOnline)
            #     # # self.get_all_profiles()
            #     # self.report.resume()
            print(resp)
            return resp
        except:
            return "ERROR"



    def getList(self):
        try:
            url = "https://cs302.pythonanywhere.com/getList/?username=" + self.username + "&password=" + self.hashPassword + "&enc=0" + "&json=1"
            resp = urllib2.urlopen(url).read()
            onlineUsersDic = json.loads(resp)
            return onlineUsersDic
        except:
            return "ERROR"
     


def runMainApp():
    config = {
        '/':{
            'tools.sessions.on':True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static':{
            'tools.staticdir.on':True,
            'tools.staticdir.dir': './static'
        }
    }
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")



    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
                           })

    print "========================="
    print "University of Auckland"
    print "COMPSYS302 - Software Design Application"
    print "========================================"                       
    
    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()
 
#Run the function to start everything
runMainApp()


