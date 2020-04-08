import socket, logging, threading
import json
import queue
import pathlib
import os.path


# Comment out the line below to not print the INFO messages
logging.basicConfig(level=logging.INFO)


class HttpRequest():

    def __init__(self, requeststr):
        self.rstr = requeststr
        self.rjson = {}
        self.parse_string()


    def parse_string(self):
        req = self.rstr.split("\r\n")
        requestLine = req[0].split()
        req.pop(0)
        reqLine = {}
        reqLine['method'] = requestLine[0]
        reqLine['URI'] = requestLine[1]
        reqLine['version'] = requestLine[2]
        self.rjson['request-line'] = reqLine

        headers = []
        for line in req:
            head = {}
            start = ""
            for element in line:
                start += element
                
                if element == ':' and start != "":
                    end = line[len(start):len(line)]
                    head[start] = end
                    headers.append(head)
                    break
                
        self.rjson['headers'] = headers


    def display_request(self):
        print("\n\nJSON: \n",self.rjson)

    def process_request(self):
        response = b""

        print("method:", self.rjson["request-line"]["method"])
        URI = "PROJ02" + self.rjson["request-line"]["URI"]
        print("URI:", URI)

        try:
            with open(URI, "r") as f:
                print(f.readlines())
        except IOError:
            print("FILE NOT FOUND")
        
        # if (os.path.exists(".."+self.rjson["request-line"]["URI"])):
        #     response = b"HTTP/1.1 200 \r\nServer: cihttpd\r\n\r\n<html><body><h1>200 A-OK! File Found</h1><p>\n\t\t-The Garbage Tier Server</p></body></html>"



        # try:
        #     with open('testPath.txt') as f:
        #         print(f.readlines())
        #         # Do something with the file
        # except IOError:
        #     print("File not accessible")


        # try:
        #     f = open("/"+self.rjson["request-line"]["URI"])
        #     print(f)
        #     response = b"HTTP/1.1 200 OK\r\n Server: cihttp \r\n\r\n"+f
        # except IOError:
        #     print("ERROR 404")
        #     response = b"HTTP/1.1 404 \r\nServer: cihttpd\r\n\r\n<html><body><h1>404 UwU</h1><p>\n\t\t-The Garbage Tier Server</p></body></html>"
        # finally:
        #     f.close()

        # else:
        response = b"HTTP/1.1 404 \r\nServer: cihttpd\r\n\r\n<html><body><h1>404 NOT-A-OK! Error Not Found</h1><p>\n\t\t-The Garbage Tier Server</p></body></html>"

                
        #     return response
        # else:
        #     return(b"HTTP/1.1 500 Not a real fake server (yet).\r\nServer: cihttpd\r\n\r\n<html><body><h1>500 UWU Internal Server Error</h1><p>Garbage Tier Server.</p></body></html>")
        
        return response





class ClientThread(threading.Thread):
    def __init__(self, address, socket, turn, queue, clientNumber):
        threading.Thread.__init__(self)
        self.csock = socket
        self.turn = turn
        self.queue = queue
        self.client = clientNumber
        logging.info('New connection added.')



    def run(self):
        if self.client == -1:
            request = self.csock.recv(1024)
            req = request.decode('utf-8')
            self.csock.send(b"HTTP/1.1 503 SERVER BUSY\r\nServer: cihttpd\r\n\r\n<html><body><h1>503 SERVR BUSY, TRY AGAIN</h1><p> \r\t\t\t- The Garbage Tier Server.</p></body></html>")
        else:
            with self.turn:
                # exchange messages
                request = self.csock.recv(1024)
                req = request.decode('utf-8')

                while self.queue.whos_turn() != self.client:
                    # client is waiting for server to not be busy
                    self.turn.wait() # wait

                print("\n\n---\nClient:[",self.client,"]")
                httpreq = HttpRequest(req)
                # httpreq.display_request()

                # TODO: Process Request GET
                # TODO: Process Request POST
                self.csock.send(httpreq.process_request())
                
                logging.info('Disconnect client.')
                self.turn.notify()

            # disconnect client
            self.queue.exit_queue()
        self.csock.close()


def server():
    logging.info('Starting cihttpd...')

    # start serving (listening for clients)
    port = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost',port))

    q = queue.QueueMachine()
    clientNumber = 0

    turn = threading.Condition() # two phases turn.wait()  & turn.notify()
    
    logging.info('Server is listening on port ' + str(port))

    while True:
        sock.listen(1)
        # client has connected
        sc,sockname = sock.accept()
        # logging.info('Accepted connection.')
        clientNumber = q.enter_queue()
        # print('Client:',clientNumber,' entering the server.')
        t = ClientThread(sockname, sc, turn, q, clientNumber)
        t.start()


server()