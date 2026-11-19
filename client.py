import socket

ADDR = "127.0.0.1"
PORT = 9999

#Client TCP example
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ADDR,PORT))
client.send('Hello from client'.encode())
print(client.recv(1024))


"""
client UDP example
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto('Hello from Client'.encode(),(ADDR, PORT))

data, adr = client.recvfrom(1024)
print(data.decode())
"""