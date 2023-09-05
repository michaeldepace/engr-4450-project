import socket
import pickle
import os
#instead of having the server aimlessly look for messages forever, we instead tell it just to look for a special fixed lenght header
#that header lets the socket know there's a new message and what the length of that messages is, so it knows when it has finished
#recieving it. The HEADERSIZE variable is the length of that special fixed header

#the fixed length header allows the program to know in advance what part of the message (how many characters) are part of the actual
#header and metadata

#we set the headersize to 10 characters because the maximum amount of bytes we want to specify a message could be (in this example)
#is 1,000,000,000 (a million bytes is ten characters)
HEADERSIZE = 10 


try:
    #configure socket (endpoint for communication)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #ipv4 and tcp
    s.connect((socket.gethostname(), 1234)) #what is 1234? #I think this line connects the client socket s (just created) 
    #with the server socket
except:
    print("Failed to establish connection with server.")

while True: #main execution loop
    full_message = b"" #specifying byte string
    new_message =  True #true on first time bc the first message you recieve is obv new
    while True: #keep the socket open to recieving data/checking if messages have been sent
        msg = s.recv(1024) #buffer of 1024 bytes of data can be recieved at a time

        #what happens if the above line executes and there is nothing recieved

        if new_message:
            #rint("new message length: ", msg[:HEADERSIZE]) #this grabs the fixed header portion of the new message
            msg_len = int(msg[:HEADERSIZE]) #grabs the message length included in the header 
            new_message = False
        #print("full message length", msg_len)
        full_message += msg#.decode("utf-8") #not being decoded for byte data
        #print(len(full_message))

        if (len(full_message) - HEADERSIZE) == msg_len: #check if the entire message contents have been recieved
            print("full message recieved")

            # tst_obj = pickle.loads(full_message[HEADERSIZE:]) #for loading python objects
            #print(tst_obj)

            img_bytes = full_message[HEADERSIZE:]

            #from PIL import Image
            #import cStringIO as StringIO
            #stream = StringIO.StringIO(b_data)
            
            #print(img_bytes)
            #image = Image.frombytes('YCbCr', (128,128), img_bytes, 'raw')
            #print("image size", image.size)
            
            #image.save('./tst.jpg')

            #print(full_message[HEADERSIZE:]) #print the actual body of the message

            file = open("./tst.jpg", "wb")
            file.write(img_bytes)
            file.close()

            new_message = True
            full_message = b"" #specifying byte stream