import socket, logging, threading
import json
import queue
import pathlib
import os.path
import time
from datetime import datetime, date
from time import gmtime, strftime



# Comment out the line below to not print the INFO messages
logging.basicConfig(level=logging.INFO)


class HttpRequest():

    def __init__(self, requeststr):
        self.rstr = requeststr
        self.rjson = {}
        self.parse_string()

    def parse_string(self):
        req = self.rstr.split("\r\n")
        print(req)
        requestLine = req[0].split()
        req.pop(0)
        reqLine = {}
        reqLine['method'] = requestLine[0]
        reqLine['URI'] = requestLine[1]
        reqLine['version'] = requestLine[2]
        self.rjson['request-line'] = reqLine

        if reqLine["method"] == "POST":
            body = req[-1]
            self.rjson['body'] = body
            # self.rjson['body-length'] = "size of body in bytes"
            print("JSON:", self.rjson['body'])

        headers = {}
        for line in req:
            start = ""
            for element in line:
                if element == ':' and start != "":
                    end = line[len(start)+2:len(line)]
                    headers[start] = end
                    break
                start += element

        self.rjson['headers'] = headers

    def display_request(self):
        print("\n\nJSON: \n",self.rjson)

    def form_parse(self):
        body = self.rjson['body'].split('&')
        name = body[0]
        name = name.split('=')
        name = name[1].replace('+',' ')
        course = body[1]
        course = course.split('=')
        course = course[1].replace('+',' ')
        return (name, course)

    def get_time(self):
        timestamp = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        return timestamp

    def post_default(self):
        f = open("PROJ02/www/post_default.html")                    
        r = f.read()
        f.close()
        return r

    def process_request(self):
        method = self.rjson["request-line"]["method"]
        path = self.rjson["request-line"]["URI"]
        URI = "PROJ02/www" + path
        timestamp = self.get_time()
        if os.path.exists(URI) :
            file_stats = os.stat(URI)
            
            last_time_mod = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime(file_stats.st_mtime))

            content_length = str(file_stats.st_size)
            msg = "HTTP/1.1 200 OK\r\nServer: cihttpd\r\nContent Length:"+content_length+"\r\nTimestamp: "+(timestamp)+"\r\nLast Modified: "+(last_time_mod)+"\r\n\r\n"
        
            if method == "HEAD":
                response = bytes(msg, 'utf-8')
            elif method == "GET":
                if (URI == "PROJ02/www/"):
                    URI = URI + "welcome.html"
                a_body = open(URI)
                response = bytes(msg + a_body.read(), 'utf-8')
                a_body.close()
            elif method == "POST":
                if path == "/form.html":      
                    name, course = self.form_parse()
                    b_body = "<html><head><title>Fancy Town</title><link rel=\"stylesheet\" href=\"style.css\"></head><body><p><h1>INPUT:</h1><ul style=\"list-style-type:none;\"><li>NAME:"+name+"</li><li>COURSE:"+course+"</li></ul></p></body></html>"
                    response = bytes(msg + b_body, 'utf-8')
                else:
                    c_body = self.post_default()
                    response = bytes(msg + c_body, 'utf-8')

        else:
            if method == "HEAD":
                response = bytes("HTTP/1.1 404 File not found\r\nServer: cihttpd\r\nTimestamp: "+(timestamp)+"\r\n\r\n", 'utf-8')
            else:
                response = bytes("HTTP/1.1 404 File not found\r\nServer: cihttpd\r\nTimestamp: "+(timestamp)+"\r\n\r\n<html><body><h1>404 File not found</h1><p>-The Garbage Tier Server</p></body></html>", 'utf-8')
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
                print("Client Queue:",self.queue.get_queue())

                httpreq = HttpRequest(req)
                # r = httpreq.process_request()
                # print("\n\n\n",r,"\n\n\n")
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