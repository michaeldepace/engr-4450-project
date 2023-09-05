import socket #for network communications
import time #just for testing sending periodic data over socket
import pickle #for converting objects to bytes so they can be sent over socket
from PIL import Image

#instead of having the server aimlessly look for messages forever, we instead tell it just to look for a special fixed lenght header
#that header lets the socket know there's a new message and what the length of that messages is, so it knows when it has finished
#recieving it. The HEADERSIZE variable is the length of that special fixed header

#the fixed length header allows the program to know in advance what part of the message (how many characters) are part of the actual
#header and metadata

#we set the headersize to 10 characters because the maximum amount of bytes we want to specify a message could be (in this example)
#is 1,000,000,000 (a million bytes is ten characters)

HEADERSIZE = 10 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #ipv4 and tcp
s.bind((socket.gethostname(), 1234)) #what is 1234 port?
s.listen(5) #accepts 5 clients at any one time

while True:
    clientSocket, address = s.accept()
    print(f"Connection from {address} established!")

    #
    # sending string data
    #
    #msg = "Welcome to the server!" #sending string data 
    #msg = f"{len(msg):<{HEADERSIZE}}" + msg #this does a bunch of stuff
    #first, it creates the fixed length header by getting the length that the message will be
    #then it pads this number with space so it fits the prespecified headersize
    #finally it appends this fixed size header to the main message you're sending
    #clientSocket.send(bytes(msg, "utf-8"))

    #
    # periodically sending time data
    #
    # while True: #used for repeatedly broadcasting time data
    #     time.sleep(3)
    #     msg = f"Current time: {time.time()}"
    #     msg = f"{len(msg):<{HEADERSIZE}}" + msg #appending header
    #     print("sending: ", msg)
    #     clientSocket.send(bytes(msg, "utf-8"))

    #
    # sending object data
    #
    # tst_obj = {1: "test", 2: "hello", 3: "world"}
    # msg = pickle.dumps(tst_obj)
    # msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg
    # #print(msg)
    # clientSocket.send(msg)


    #
    # testing sending an image to client
    #


    # with open("./Image-228.jpg", "rb") as f:
    #     img_bytes = f.read()
    # import io
    # from PIL import Image

    # img = Image.open('./Image-228.jpg')
    # img_bytes = img.tobytes()
    # msg = bytes(f"{len(img_bytes):<{HEADERSIZE}}", "utf-8") + img_bytes
    # clientSocket.send(msg)
    # img = Image.open("Image-228.jpg")
    # img.tobytes


    file = open('./Image-228.jpg', "wb")
    img_chunk = file.read(2048)
    while img_chunk:
        clientSocket.send(img_chunk)
        img_chunk = file.read(2048)


#i think you can't close these with ctrl+c after running bc the terminal is preoccupied with running the process & waiting for messages
#implement some code to make it time out