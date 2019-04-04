import os
import sys
import _thread
import socket
import json
import time
import base64


# ********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 999999  # max number of bytes we receive at once
DEBUG = True            # set to True to see the debug msgs


# **************************************
# ********* MAIN PROGRAM ***************
# **************************************
def main():

    # read file

    with open('config.json', 'r') as myfile:
        data = myfile.read()
    obj = json.loads(data)

    # host and port info.
    port = obj["port"]
    host = 'localhost'

    # make log file
    file = open(obj["logging"]["logFile"], "w")

    def _write_file(text):
        write_file(file, text, obj["logging"]["logFile"])

    _write_file("Proxy launched")

    try:
        # create a socket
        _write_file("Creating server socket...")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # associate the socket to host and port
        _write_file(" Binding socket to port " + str(port) + "...")
        soc.bind((host, port))

        # listenning

        _write_file("Listening for incoming requests...")
        soc.listen(BACKLOG)

    except (socket.error):
        if soc:
            soc.close()
        _write_file("Could not open socket")
        sys.exit(1)

    # get the connection from client
    while 1:
        conn, client_addr = soc.accept()
        _write_file("Accepted a request from client!")

        # create a thread to handle request
        _thread.start_new_thread(
            proxy_thread, (conn, client_addr, obj, _write_file))

    soc.close()


# *******************************************
# ********* PROXY_THREAD FUNC ***************
# A thread to handle request from browser
# *******************************************
def proxy_thread(conn, client_addr, config, _write_file):

    # get the request from browser
    request = conn.recv(MAX_DATA_RECV).decode('ascii')
    _write_file("\n---------------------\n" + request)

    # edit http version
    edited_request = change_request(request, config)
    print(edited_request)

    # find the webserver and port
    webserver, port = find_webserver_and_port(edited_request)

    # restriction
    if(config["restriction"]["enable"]):
        for target in config["restriction"]["targets"]:
            if(target["URL"] == webserver):
                if(target["notify"]):
                    send_email(request)
                conn.send("HTTP/1.0 403 Forbidden".encode('ascii'))
                conn.close()
                _write_file("restricted")
                sys.exit(1)

    try:
        # create a socket to connect to the web server
        _write_file("Proxy opening connection to server" + webserver)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        _write_file("Connection opened...")

        # send request to webserver
        _write_file(
            "Proxy sent request to server with headers: \n" + edited_request)
        s.send(edited_request.encode('ascii'))

        while 1:
            # receive data from web server
            data = s.recv(MAX_DATA_RECV)
            _write_file(
                " Server sent response to proxy with headers:\n")

            if (len(data) > 0):
                # send to browser
                _write_file(
                    " Proxy sent response to client with headers:\n")

                conn.send(data)
            else:
                break
        s.close()
        conn.close()
    except socket.error:
        if s:
            s.close()
        if conn:
            conn.close()
        sys.exit(1)


# **************************************
# ********* HELPER FUNCTIONS ***********
# **************************************

def change_request(request, config):
    temp = remove_proxy_connection_field(change_start_line(request))
    if(config["privacy"]["enable"]):
        temp = privacy(temp, config["privacy"]["userAgent"])
    return temp


def change_start_line(request):
    http_version_pos = request.find('HTTP/1.')
    temp = request[0:http_version_pos].split(' ')
    return temp[0] + ' ' + get_routes(temp[1]) + ' HTTP/1.0 ' + request[http_version_pos + 8:]


def get_routes(url):
    temp = url[(url.find("://") + 3):]
    return '/' + temp[temp.find('/')+1:]


def find_webserver_and_port(request):
    temp = request[request.find('Host:') + 6:]
    temp = temp[0:temp.find('\r\n')]
    port_pos = temp.find(':')
    if(port_pos == -1):
        return temp, 80
    return temp[0:port_pos], int(temp[port_pos+1:])


def remove_proxy_connection_field(request):
    temp = ''
    for line in request.split('\r\n'):
        if(line.find('Proxy-Connection') == -1):
            temp += line + '\r\n'
    return temp


def write_file(file, text, enable):
    temp_time = time.strftime("[%a, %d %b %Y %H:%M:%S] ", time.gmtime())
    print(temp_time + text)
    if(enable):
        file.write(temp_time + text + '\n')


def privacy(request, new_user_agent):
    temp = ''
    for line in request.split('\r\n'):
        if(line.find('User-Agent') == -1):
            temp += line + '\r\n'
        else:
            temp += "User-Agent: " + new_user_agent + '\r\n'
    return temp


def send_email(message):
    msg = "\r\n " + message
    endmsg = "\r\n.\r\n"

    mailserver = ("mail.ut.ac.ir", 25)
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(mailserver)
    recv = clientSocket.recv(1024)
    recv = recv.decode()

    if recv[:3] != '220':
        print('220 reply not received from server.')

    heloCommand = 'EHLO mail.ut.ac.ir\r\n'
    clientSocket.send(heloCommand.encode())
    recv1 = clientSocket.recv(1024)
    recv1 = recv1.decode()

    if recv1[:3] != '250':
        print('250 reply not received from server.')

    # Info for username and password
    username = "hosein.norouzi76"
    password = "Hn2130567827"
    base64_str = ("\x00"+username+"\x00"+password).encode()
    base64_str = base64.b64encode(base64_str)
    authMsg = "AUTH PLAIN ".encode()+base64_str+"\r\n".encode()
    clientSocket.send(authMsg)
    clientSocket.recv(1024)

    mailFrom = "MAIL FROM: <hosein.norouzi76@ut.ac.ir> \r\n"
    clientSocket.send(mailFrom.encode())
    recv2 = clientSocket.recv(1024)
    recv2 = recv2.decode()

    rcptTo = "RCPT TO: <hosein.norouzi76@yahoo.com> \r\n"
    clientSocket.send(rcptTo.encode())
    recv3 = clientSocket.recv(1024)
    recv3 = recv3.decode()

    data = "DATA\r\n"
    clientSocket.send(data.encode())
    recv4 = clientSocket.recv(1024)
    recv4 = recv4.decode()

    subject = "Subject: restriction\r\n\r\n"
    clientSocket.send(subject.encode())
    date = time.strftime("[%a, %d %b %Y %H:%M:%S]", time.gmtime())
    date = date + "\r\n\r\n"
    clientSocket.send(date.encode())
    clientSocket.send(msg.encode())
    clientSocket.send(endmsg.encode())
    clientSocket.recv(1024)

    quit = "QUIT\r\n"
    clientSocket.send(quit.encode())
    recv5 = clientSocket.recv(1024)
    print(recv5.decode())
    clientSocket.close()


if __name__ == '__main__':
    main()
