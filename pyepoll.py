__author__ = 'jmpews'
# Simple http web server based on EPoll
import socket
import select

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

# serversocket=socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0,fileno=None)
# serversocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# serversocket.bind(('127.0.0.1',8080))
# serversocket.listen(5)
# serversocket.setblocking(0)
socks={}
for i in range(5):
    sock=socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0,fileno=None)
    sock.connect(('localhost',7777))
    print(sock.fileno(),'connected..')
    socks[sock.fileno()]=sock
epoll=select.epoll()
epoll.register(list(socks.values()),select.EPOLLIN)
try:
    connections={}
    requests={}
    responses={}
    while True:
        events=epoll.poll(1)
        for fileno,event in events:
            if event&select.EPOLLIN:
                print('ready for data...')
                requests[fileno]+=connections[fileno].recv(1024)
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    # epoll.modify(fileno,select.EPOLLOUT)
                    print('-'*40+'\n'+requests[fileno].decode()[:-2])
            elif event&select.EPOLLOUT:
                # default 边缘触发模式，如果没发完，会一直提醒，与边沿触发模式不同
                # 由于发送缓存区和接收缓存区的问题，要不断发送，直到数据发送完毕
                while len(responses[fileno])>0:
                    bytewriten=connections[fileno].send(responses[fileno])
                    responses[fileno]=responses[fileno][bytewriten:]
                if len(responses[fileno])==0:
                    epoll.modify(connections[fileno],select.EPOLLHUP)
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event&select.EPOLLHUP:
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(list(socks.keys()))
    epoll.close()
    for sock in socks.values():
        sock.close()
