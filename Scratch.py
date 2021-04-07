'''SetCloudVariable and login by https://scratch.mit.edu/users/Raihan142857/'''
import requests
import re
import websocket
import json
import time
import numpy 
import wsaccel
import CloudVariables
import threading

class ScratchExceptions(Exception): 
    pass

class InvalidCredentialsException(ScratchExceptions): 
    pass

class ScratchSession(): 

    def __init__(self, username, password, project_id): 
        self.username = username 
        self.password = password
        self.project_id  = project_id
        self.ws = websocket.WebSocket()
        self.cloudvariables = []
        self.timer = time.time()
        self.login()
        self.connect()

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

    def _sendPacket(self, packet): 
        self.ws.send(json.dumps(packet) + '\n') 

    def connect(self):
        self.ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid='+self.sessionId+';', origin='https://scratch.mit.edu', enable_multithread=True) # connect the websocket
        self._sendPacket({
            'method': 'handshake',
            'user': self.username,
            'project_id': str(self.project_id)
        }) 
        response = self.ws.recv().split("\n")
        for variable in response:
            try: 
                variable = json.loads(str(variable))
            except:
                pass
            else:
                self.cloudvariables.append(CloudVariables.CloudVariable(variable["name"], variable["value"]))

    def SetCloudVar(self, variable: str, value):
        if time.time - self.timer > 0.1:
            if not value.isdigit():
                raise ValueError("Cloud variables can only be set to a combination of numbers")
            try: 
                self._sendPacket({
                    'method': 'set',
                    'name': ('☁ ' + variable if not variable.startswith('☁ ') else variable),
                    'value': str(value),
                    'user': self.username,
                    'project_id': str(self.project_id)
                })
            except (BrokenPipeError, websocket._exceptions.WebSocketConnectionClosedException):
                self.connect()
                time.sleep(0.1) 
                self.SetCloudVar(variable, value)
                return
            else:
                self.timer = time.time()
                for cloud in self.cloudvariables:
                    if cloud.name == variable:
                        cloud.value = value
                        break
        else:
            time.sleep(time.time - self.timer)
            self.SetCloudVar(variable, value)
    
    def _GetCloudVariableLoop(self):
        while True:
            if self.ws.connected:
                response = self.ws.recv()
                response = json.loads(response)
                for cloud in self.cloudvariables:
                    if response["name"] == cloud.name:
                        cloud.value = response["value"]
            
            else:
                self.connect()
    def GetCloudVariables(self):
        """Will start a new thread that looks for the cloud variables and appends their results onto cloudvariables"""
        thread = threading.Thread(target=self._GetCloudVariableLoop)
        thread.start()
