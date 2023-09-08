import websocket
import json
import base64
from colorama import Fore
import time
from gpt4free import you
import codecs
import re
import threading
import random

SessionID = ""

ConnectionID = ""
ConnectionHash = ""
ConnectionKey = ""
ConnectionEstablished = False

ReceiverSex = None
ReceiverAge = None

chat = []

CEID = 0

def ask_ai(msg, printOnScreen):
    global chat

    response = you.Completion.create(prompt=msg, chat=chat)

    while response.text == "Unable to fetch the response, Please try again.":
        response = you.Completion.create(prompt=msg, chat=chat)
    chat.append({"question": msg, "answer": response.text})
    text = codecs.decode("\n" + response.text + "\n", 'unicode_escape')

    if printOnScreen:
        print(Fore.CYAN + "\t> " + Fore.WHITE + text)
    return(text)

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def sendPing():
    ws.send("2")
    # print(Fore.RED + "PING" + Fore.WHITE)

def sendMessage(payload):
    payload = str(json.dumps(payload))
    ws.send("4" + payload)
    # print(Fore.BLUE + "Client: " + Fore.LIGHTBLACK_EX + "4" + payload)

def getCEID():
    global CEID
    CEID += 1
    return str(CEID)

def searchConnection():
    payload = {}
    payload["ev_name"] = "_sas"
    payload["ev_data"] = {}
    payload["ev_data"]["channel"] = "main"
    payload["ev_data"]["myself"] = {}
    payload["ev_data"]["myself"]["sex"] = 0
    payload["ev_data"]["myself"]["loc"] = 0
    payload["ev_data"]["preferences"] = {}
    payload["ev_data"]["preferences"]["sex"] = 0
    payload["ev_data"]["preferences"]["loc"] = 0
    payload["ceid"] = getCEID()
    sendMessage(payload)

def send_message_to_user(msg):
    payload = {}
    payload["ev_name"] = "_pmsg"
    payload["ev_data"] = {}
    payload["ev_data"]["ckey"] = ConnectionKey
    payload["ev_data"]["msg"] = msg
    payload["ev_data"]["idn"] = 0
    payload["ceid"] = getCEID()
    if ConnectionEstablished:
        time.sleep(random.randint(1, 5))
        sendMessage(payload)

def openImage(data):
    with open('captcha.jpg', 'wb') as file:
        file.write(base64.b64decode(data))

def on_message(ws, message):
    global ConnectionID
    global SessionID
    global ConnectionHash
    global ConnectionEstablished
    global ConnectionKey
    global chat
    global ReceiverSex
    global ReceiverAge

    # print(Fore.GREEN + "Server: " + Fore.LIGHTBLACK_EX + (message[:200] + Fore.LIGHTBLACK_EX + "...") if len(message) > 200 else (Fore.GREEN + "Server: " + Fore.LIGHTBLACK_EX + message))
    if message == "3":
        # print(Fore.RED + "PONG" + Fore.WHITE)
        sendPong()

    json_message = message[1:]
    msg = json.loads(json_message)

    if msg.get("ev_name") == "count":
        print(Fore.LIGHTBLACK_EX + "Users: " + msg.get("ev_data") + Fore.WHITE)

    elif msg.get("sid"):
        SessionID = msg.get("sid")

    elif msg.get("ev_name") == "cn_acc":
        ev_data = msg.get("ev_data")
        ConnectionID = ev_data.get("conn_id")
        ConnectionHash = ev_data.get("hash")
        print(Fore.LIGHTBLACK_EX + "Hash has been set: " + ConnectionHash + Fore.WHITE)
        payload = {}
        payload["ev_name"] = "_cinfo"
        payload["ev_data"] = {}
        payload["ev_data"]["hash"] = ConnectionHash
        payload["ev_data"]["dpa"] = True
        payload["ev_data"]["caper"] = True
        sendMessage(payload)
        searchConnection()

    elif msg.get("ev_name") == "caprecvsas" or msg.get("ev_name") == "capchresp":
        ConnectionEstablished = False
        ev_data = msg.get("ev_data")
        if ev_data.get("wait"):
            time.sleep(1)
            payload = {}
            payload["ev_name"] = "_capch"
            sendMessage(payload)
        tlce = ev_data.get("tlce")
        data = tlce.get("data")
        data = data.replace("data:image/jpeg;base64,", "").replace("'", "").replace("[", "").replace("]", "")
        openImage(data)
        payload = {}
        payload["ev_name"] = "_capsol"
        payload["ev_data"] = {}
        payload["ev_data"]["solution"] = input(Fore.CYAN + "Captcha code: " + Fore.WHITE)
        sendMessage(payload)
    
    elif msg.get("ev_name") == "capissol":
        ev_data = msg.get("ev_data")
        success = ev_data.get("success")
        captcha_veryfication = (Fore.GREEN + "ACCEPTED") if success else (Fore.RED + "REJECTED")
        print(Fore.LIGHTBLACK_EX + "[" + Fore.RED + "!" + Fore.LIGHTBLACK_EX + "] " + Fore.CYAN + "Captcha verification: " + captcha_veryfication + Fore.WHITE)
        if success:
            searchConnection()
        else:
            payload = {}
            payload["ev_name"] = "_capch"
            sendMessage(payload)
    
    elif msg.get("ev_name") == "talk_s":
        print(Fore.GREEN + "POŁĄCZONO" + Fore.WHITE)
        send_message_to_user("Witaj w Chat GPT w 6obcy, jakie jest twoje pytanie?")
        ai_init = """
        Pisz zemną jak z człowiekiem. Odpowiadaj krótko.
        Nie lubię długich wiadomości.
        Jak możesz to odpowiadaj nawet tak lub nie tylko.
        Zaproponuj rozmowę o dzisiajszym dniu lub rzeczach które mnie trapią.
        """
        ask_ai(ai_init, False)
        ConnectionEstablished = True
        ev_data = msg.get("ev_data")
        ConnectionID = ev_data.get("cid")
        ConnectionKey = ev_data.get("ckey")

        payload = {}
        payload["ev_name"] = "_begacked"
        payload["ev_data"] = {}
        payload["ev_data"]["ckey"] = ConnectionKey
        payload["ceid"] = getCEID()
        sendMessage(payload)
    
    elif msg.get("ev_name") == "sdis":
        ReceiverSex = None
        ReceiverAge = None
        print(Fore.RED + "ROZŁĄCZONO" + Fore.WHITE)
        chat.clear()
        ConnectionEstablished = False
        searchConnection()
    
    elif msg.get("ev_name") == "styp":
        isTyping = msg.get("ev_data")
        if isTyping:
            print("Obcy pisze...")

    elif msg.get("ev_name") == "rmsg":
        ev_data = msg.get("ev_data")
        msg = ev_data.get("msg")
        who = ev_data.get("who")
        msg = msg.lower()
        if ReceiverSex == None:
            if "k" in msg:
                ReceiverSex = "Kobieta"
                msg += " hej jestem dziewczyną"
            elif "m" in msg:
                ReceiverSex = "Mężczyzna"
                msg +=" hej jestem chłopakiem"
        if ReceiverAge == None:
            if re.findall(r'\d+', msg):
                ReceiverAge = re.findall(r'\d+', msg)
                msg = msg.replace(re.findall(r'\d+', msg), "mam " + re.findall(r'\d+', msg) + " lat")

        print(Fore.LIGHTGREEN_EX + str(who) + "\t> " + Fore.WHITE + msg)
        if len(msg) > 0:
            send_message_to_user(ask_ai(msg.replace("km", ""), True))

if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://server.6obcy.pl:7002/6eio/?EIO=3&transport=websocket", on_message=on_message)
    set_interval(sendPing, 15)
    ws.run_forever()
