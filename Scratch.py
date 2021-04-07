'''Credit to https://scratch.mit.edu/users/Raihan142857/'''
import requests
import re
import websocket
import json
import time
import numpy # these last two lines speed up the websocket sending, they are optional, how they dont seem to be used in the code
import wsaccel

class ScratchExceptions(Exception): #plural because I was going to add more
    pass

class InvalidCredentialsException(ScratchExceptions): #exception if wrong login information
    pass


class ScratchSession(): #parantheses used for sub classes

    def __init__(self, username, password, project_id): #parameters for the class, only can be used in init so we set to a self. variable
        self.username = username #self shared across whole class like this
        self.password = password
        self.project_id  = project_id
        self.ws = websocket.WebSocket()

    def login(self):
        headers = {
        "x-csrftoken": "a",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": "scratchcsrftoken=a;scratchlanguage=en;",
        "referer": "https://scratch.mit.edu"
        }
        data = json.dumps({
        "username": self.username,
        "password": self.password
        })

        request = requests.post('https://scratch.mit.edu/login/', data=data, headers=headers)

        try:
            self.sessionId = re.search('\"(.*)\"', request.headers['Set-Cookie']).group()
        except AttributeError:
            raise InvalidCredentialsException("Your password or username is incorrect")

    def _sendPacket(self, packet): #_ = private function since python no have private function
        self.ws.send(json.dumps(packet) + '\n') 

    def connect(self):
        #global ws not needed
        self.ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid='+self.sessionId+';', origin='https://scratch.mit.edu', enable_multithread=True) # connect the websocket
        self._sendPacket({
            'method': 'handshake',
            'user': self.username,
            'project_id': str(self.project_id)
        }) # to set variables you need to handshake first
        response = self.ws.recv()#work here(note for myself)

    def setCloudVar(self, variable, value):
        try: 
            self._sendPacket({
                'method': 'set',
                'name': '☁ ' + variable,
                'value': str(value),
                'user': self.username,
                'project_id': str(self.project_id)
            })
        except (BrokenPipeError, websocket._exceptions.WebSocketConnectionClosedException):
            # sometimes you get a BrokenPipeError randomly and this fixes it, caused by websocket closing
            self.connect()
            time.sleep(0.1) #Is this so scratch has time to read hand shake?
            self.setCloudVar(variable, value)
    

if __name__ == "__main__":
    session = ScratchSession()
    session.login()
    session.setCloudVar()
