import os
import sys
import _thread
import socket


# ********* CONSTANT VARIABLES *********
BACKLOG = 50            # how many pending connections queue will hold
MAX_DATA_RECV = 999999  # max number of bytes we receive at once
DEBUG = True            # set to True to see the debug msgs


# **************************************
# ********* MAIN PROGRAM ***************
# **************************************
def main():

    # host and port info.
    port = 8080
    host = 'localhost'

    print("Proxy Server Running on ", host, ":", port)

    try:
        # create a socket
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # associate the socket to host and port
        soc.bind((host, port))

        # listenning
        soc.listen(BACKLOG)

    except (socket.error):
        if soc:
            soc.close()
        print("Could not open socket:")
        sys.exit(1)

    # get the connection from client
    while 1:
        conn, client_addr = soc.accept()

        # create a thread to handle request
        _thread.start_new_thread(proxy_thread, (conn, client_addr))

    soc.close()


# *******************************************
# ********* PROXY_THREAD FUNC ***************
# A thread to handle request from browser
# *******************************************
def proxy_thread(conn, client_addr):

    # get the request from browser
    request = conn.recv(MAX_DATA_RECV)
    # parse the first line
    temp = replace_http_version(str(request, 'utf-8'))
    print(temp)
    # edit http version

    list_req = str(temp).split('\r\n')
    first_line = list_req[0]

    # get url
    url = first_line.split(' ')[1]

    # find the webserver and port
    http_pos = url.find("://")          # find pos of ://
    if (http_pos == -1):
        temp = url
    else:
        temp = url[(http_pos+3):]       # get the rest of url

    port_pos = temp.find(":")           # find the port pos (if any)

    # find end of web server
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if (port_pos == -1 or webserver_pos < port_pos):      # default port
        port = 80
        webserver = temp[:webserver_pos]
    else:       # specific port
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    try:
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(temp.encode('utf-8'))         # send request to webserver

        while 1:
            # receive data from web server
            data = s.recv(MAX_DATA_RECV)

            if (len(data) > 0):
                # send to browser
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
        # print("Peer Reset", first_line, client_addr)
        sys.exit(1)


# **************************************
# ********* HELPER FUNCTIONS ***********
# **************************************

def replace_http_version(request):
    temp = request.split('HTTP/1.')
    return temp[0] + 'HTTP/1.0' + temp[1][1:]


if __name__ == '__main__':
    main()
