import socket

class EightChanRelay:

    def __init__(self, hostname, port, NumberOfRelays, id):
        ''''init '''
        self.hostname = hostname
        self.port = int(port)
        self.NumberOfRelays = int(NumberOfRelays)
        self.name = id
        self.buffersize = 512
        self.relays = []
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        for r in range(1, self.NumberOfRelays + 1):
            x = Relay(r, "r" + str(r))
            self.relays.append(x)

    def connect(self):
        '''connect'''
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.hostname, self.port))
            return(1)
        except:
            print("Connection failed")
            return(0)

    def disconnect(self):
        self.s.close()

    def send(self, msg):
        self.s.send(msg)
        return self.s.recv(self.buffersize)

    def processUpdate(self, value, index):
        '''Check if index is ok'''
        if index > self.NumberOfRelays:
            raise Exception("Invalid index number, maximum of " + str(self.NumberOfRelays) + " relays.")

        if self.connect():
            print("Sending command to relay")
            if value == "on":
                msg = "L" + str(index)
                self.relays[(index - 1)].status = 1
            else:
                msg = "D" + str(index)
                self.relays[(index - 1)].status = 0

            response = self.send(msg.encode())
            self.disconnect()
        else:
            raise Exception("Cannot connect to relay board")

    def updateStatus(self):
        if self.connect():
            for rl in self.relays:
                msg = 'R' + str(rl.ind)
                response = self.send(msg.encode())

                if str(response).find("off") != -1:
                    rl.status = 0
                else:
                    rl.status = 1
            self.disconnect()
        else:
            print("Cannot connect")

class Relay:
    def __init__(self, index, name):
        self.ind = index
        self.name = name
        self.status = 0
