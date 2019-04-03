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
    request = str(conn.recv(MAX_DATA_RECV), 'utf-8')

    # edit http version
    edited_request = change_request(request)
    print(edited_request)

    # find the webserver and port
    webserver, port = find_webserver_and_port(edited_request)
    print(webserver, port)
    try:
        # create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        # send request to webserver
        s.send(edited_request.encode('utf-8'))

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
        sys.exit(1)


# **************************************
# ********* HELPER FUNCTIONS ***********
# **************************************

def change_request(request):
    return change_start_line(request)


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


if __name__ == '__main__':
    main()
