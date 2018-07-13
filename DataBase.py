import sqlite3
import smtplib

# put try and except everwhere

# database = "users.db"
def setupDataBase(listUsers):
    try:
        createTable = createDBTable()
        if(createTable):
            initUser(listUsers)
    except:
        pass


def initUser(listUser):
    try: 
        conn = sqlite3.connect('userInfo.db')
        c = conn.cursor()
        for username in listUser:
            c.execute("SELECT rowid FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if(user == None):
                c.execute('''INSERT INTO users (username, location, ip, port, loginTime) VALUES (?,?,?,?,?)''', (username, "-", "-", "-", "-"))
        conn.commit()
        conn.close()
    except:
        pass
            
        
def createDBTable():
    # Maybe make a function for open db and close?
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    location TEXT,
                    ip TEXT,
                    port TEXT,
                    loginTime TEXT,
                    publicKey TEXT)''')
                    # publicKey TEXT add to db 
        c.execute('''CREATE TABLE IF NOT EXISTS userProfile (
                    id INTEGER PRIMARY KEY,
                    FullName TEXT, 
                    username TEXT,  
                    position TEXT, 
                    description TEXT, 
                    profilePic TEXT,
                    status TEXT) ''')
                    # change test html format
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, 
                    sender TEXT, 
                    destination TEXT, 
                    message TEXT, 
                    stamp TEXT,
                    file TEXT, 
                    filename TEXT, 
                    content_type TEXT)''')
    except:    
        conn.close()
        return False
    conn.commit()
    conn.close()

    return True

def getMessages(username,destination):
    allMsgs = ''
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM messages WHERE sender='{a}' AND destination='{b}' OR sender='{b}' AND destination='{a}'".format(a=destination, b=username))
        allMsgs = [dict(zip(['id','sender', 'destination', 'message', 'stamp','file','filename','content_type','status'],row)) for row in c.fetchall()]
        conn.commit()
        conn.close()
        return allMsgs
    except:
        pass

def getProfile(userProfile):
    try:
        conn = sqlite3.connect('userInfo.db')
        c = conn.cursor()
        c.execute("SELECT * FROM userProfile WHERE username = ?", (userProfile,))
        userprofile = c.fetchone()
        conn.commit()
        conn.close()
        return userprofile
    except:
        pass

    



def getUserInfo(usersName):
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (usersName,))
    # change line above if u change database
    userInfo = c.fetchone()
    conn.commit()
    conn.close()
    return userInfo


def updateUserTable(newUser):
    try:
        conn = sqlite3.connect('userInfo.db')
        c = conn.cursor()
        count = 0
        while str(count) in newUser:
            online = newUser[str(count)]
            # Same thing as
            c.execute("SELECT rowid FROM users WHERE username = ?", (online['username'],))
            userData = c.fetchone()
            if(userData == None):
                count += 1
                continue
            else:
                c.execute('''UPDATE users SET username=?, location=?, ip=?, port=?, loginTime=? WHERE rowid=?''', [online['username'],online['location'], online['ip'],online['port'], online['lastLogin'], userData[0] ])
            count +=1
        conn.commit()
        conn.close()
    except:
        pass

def getSenderIP(username):
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    c.execute("SELECT ip FROM users WHERE username = ?", (username,))
    userIP = c.fetchone()
    userIP = ''.join(userIP)
    conn.commit()
    conn.close()
    return userIP


def getSenderPort(username):
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    c.execute("SELECT port FROM users WHERE username = ?", (username,))
    userPort = c.fetchone()
    userPort = ''.join(userPort)
    conn.commit()
    conn.close()
    return userPort


def getUserProfile(userName):
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    c.execute("SELECT * FROM userProfile WHERE username = ?", (userName,))
    # change line above if u change database
    userInfo = c.fetchone()
    conn.commit()
    conn.close()
    return userInfo

def getEntireDataBase():
    conn = sqlite3.connect('userInfo.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    # change line above if u change database
    userInfo = c.fetchall()
    conn.commit()
    conn.close()
    return userInfo

def updateUserProfile(dictionary, userName):
    if isinstance(dictionary, unicode):
        dictionary = ast.literal_eval(dictionary)
    else:
        conn = sqlite3.connect('userInfo.db')
        c = conn.cursor()
        c.execute("SELECT rowid FROM userProfile WHERE username = ?", (userName,))
        userData = c.fetchone()
        if(userData == None):
            c.execute('''INSERT INTO userProfile (FullName, username, position, description, profilePic) VALUES (?,?,?,?,?)''', (dictionary.get('FullName'), userName, dictionary.get('position'), dictionary.get('description'), dictionary.get('profilePic')))    
            # add location if doing that
            conn.commit()
            conn.close()
        else:
            c.execute('''UPDATE userProfile SET FullName=?, username=?, position=?, description=?, profilePic=?''', (dictionary.get('FullName'), userName, dictionary.get('position'), dictionary.get('description'), dictionary.get('profilePic')))  
            conn.commit()
            conn.close()



def signUpNewUser(FullName, email, username, password):
    validUserName = getUserInfo(username)
    conn = sqlite3.connect('userInfo.db') 
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    validEmail = c.fetchone()
    if(validUserName == None) and (validEmail == None) and ((username or email or FullName or password) != ""):
        c.execute("INSERT INTO users VALUES (?,?,?,?)", (FullName, email, username, password))
        conn.commit()
        conn.close()
        confirmationMail = smtplib.SMTP('smtp.gmail.com', 587)
        confirmationMail.starttls()
        confirmationMail.login("COMPSYS302.Server@gmail.com", "Andrew132") 
        message = "Hi " +FullName+ "\n \nWelcome to the Server!\nThanks so much for joining us. \nYou arre on your way to communicate effectively with loved ones but not over the world only in your house.\n\n\n\nChief Executive Officer And Co-Developer of Hot or Not\nPJ" 
        confirmationMail.sendmail("COMPSYS302.Server@gmail.com", email, message)
        confirmationMail.quit()
        return 0
    else:
        conn.commit()
        conn.close()
        return
    
def saveMessage(dictionary):
    conn = sqlite3.connect('userInfo.db') 
    c = conn.cursor()
    c.execute("SELECT rowid FROM messages WHERE sender = ? and destination = ? and stamp = ?", (dictionary.get('sender'), dictionary.get('destination'), dictionary.get('stamp'),))
    data = c.fetchone()
    if(data == None):
        c.execute('''INSERT INTO messages (sender, destination, message, stamp, file, filename, content_type, status) VALUES (?,?,?,?,?,?,?,?)''', (dictionary.get('sender'), dictionary.get('destination'), dictionary.get('message'), dictionary.get('stamp'),dictionary.get('file'),dictionary.get('filename'),dictionary.get('content_type'),dictionary.get('status'),))
    conn.commit()
    conn.close()
    return True

