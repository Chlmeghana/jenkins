import socket
import time  # Added for optional delay between messages

# Server details
SERVER_IP = "9.56.214.105"
SERVER_PORT = 1952

# Messages to send
messages = ["macbook meghana 1", "macbook meghana 2"]

def receive_lines(sock):
    dataline = ""  
    num = 0        

    while True:  
        try:
            data = sock.recv(1024).decode('latin-1')  # Read up to 1024 bytes
            if not data:  
                break

            print(f"{data} \n")

        except Exception as e:
            print(f"Error: {e}")
            break

try:
    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

    # Send multiple messages
    for message in messages:
        client_socket.sendall(message.encode('ascii'))  # Send each message
        print(f"Sent: {message}")
        time.sleep(1)  # Optional delay for better clarity in server output

    # Receive response
    receive_lines(client_socket)

except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the connection
    client_socket.close()
