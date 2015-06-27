# Simple http web server based on EPoll(El(边沿触发))
import socket
import select
import logging
import errno

logger=logging.getLogger('epollpy-et')
def Initlog():
    logger.setLevel(logging.DEBUG)
    fh=logging.FileHandler('epollpy-et.log')
    fh.setLevel(logging.DEBUG)
    ch=logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
Initlog()
print('Initing Log...')
EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket=socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, 
                           fileno=None)                          
serversocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
serversocket.bind(('127.0.0.1',8080))
serversocket.listen(5)
serversocket.setblocking(0)

epoll=select.epoll()
epoll.register(serversocket.fileno(),select.EPOLLIN)
print('Listening 8080...')
try:
    connections={}
    requests={}
    responses={}
    while True:
        events=epoll.poll(1)
        for fileno,event in events:
            if event&select.EPOLLIN:
                if fileno==serversocket.fileno():
                    connection,address=serversocket.accept()
                    connection.setblocking(0)
                    logger.debug("accept connection from %s, %d, fd = %d" % (address[0], address[1], connection.fileno()))
                    epoll.register(connection.fileno(),select.EPOLLIN|select.EPOLLET)
                    connections[connection.fileno()]=connection 
                    requests[connection.fileno()]=b''
                    responses[connection.fileno()]=response
                else:
                    datas=b''
                    while True:
                        try:
                            data=connections[fileno].recv(1024)
                            if not data and not datas:
                                epoll.unregister(fileno)
                                connections[fileno].close()
                                logger.debug("%s, %d closed" % (address[0], address[1]))
                                break
                            else:
                                datas+=data
                        except socket.error as e:
                            if errno.EAGAIN==e.errno:
                                logger.debug("%s receive %s" % (fileno, datas))
                                requests[fileno]=datas
                                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                                    epoll.modify(fileno,select.EPOLLOUT|select.EPOLLET)
                                    print('-'*40+'\n'+requests[fileno].decode()[:-2])                                
                                epoll.modify(fileno,select.EPOLLOUT|select.EPOLLET)
                                break
                            else:
                                epoll.unregister(fileno)
                                connections[fileno].close()
                                logger.error(e)
                                break

            elif event&select.EPOLLOUT:
                # default 边缘触发模式，如果没发完，会一直提醒，与边沿触发模式不同
                # 由于发送缓存区和接收缓存区的问题，要不断发送，直到数据发送完毕
                try:
                    while len(responses[fileno])>0:
                        bytewriten=connections[fileno].send(responses[fileno])
                        responses[fileno]=responses[fileno][bytewriten:]
                except socket.error:
                    pass
                if len(responses[fileno])==0:
                    #epoll.modify(connections[fileno],select.EPOLLHUP)
                    epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
            elif event&select.EPOLLHUP:
                    epoll.unregister(fileno)
                    connections[fileno].close()
                    del connections[fileno]
                    logger.debug("%s, %d closed" % (address[0], address[1]))
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()