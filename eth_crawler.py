import time
import customtkinter
import tkinter as tk
from requests import get
from matplotlib import pyplot as plt
from datetime import datetime

# pravimo base_url i api za sve pozive
API_KEY = "AZ71VNV26URBB8NEY8ZK3CPW23REMYHJ7C"
BASE_URL = "https://api.etherscan.io/api"

# radi racunanja dobijamo wei hoćemo da prebacimo u ETH
ETHER_VALUE = 10 ** 18 


# pravimo default api za pozive
def make_api_url(module, action, address, **kwargs):
	url = BASE_URL + f"?module={module}&action={action}&address={address}&apikey={API_KEY}"

	for key, value in kwargs.items():
		url += f"&{key}={value}"

	return url


# spajamo i pravimo stanje računa korisnika - pravljeno pomoću dokumentacija sa sajta 
# https://docs.etherscan.io/api-endpoints/accounts
''' - moze se profiniti
https://api.etherscan.io/api
   ?module=account
   &action=balance
   &address=0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae
   &tag=latest
   &apikey=YourApiKeyToken
'''


def get_account_balance(address):
	balance_url = make_api_url("account", "balance", address, tag="latest")
	response = get(balance_url)
	data = response.json()

	value = int(data["result"]) / ETHER_VALUE
	return value


''' - normalne transakcije
https://api.etherscan.io/api
   ?module=account
   &action=txlist
   &address=0xc5102fE9359FD9a28f877a67E36B0F050d81a3CC
   &startblock=0
   &endblock=99999999
   &page=1
   &offset=10
   &sort=asc
   &apikey=YourApiKeyToken

   - interne transakcije
   https://api.etherscan.io/api
   ?module=account
   &action=balance
   &address=0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae
   &tag=latest
   &apikey=YourApiKeyToken
'''

def get_transactions(address):
    transactions_url = make_api_url("account", "txlist", address, startblock=0, endblock=99999999, page=1, offset=10000, sort="asc")
    response = get(transactions_url)
    data = response.json()["result"]

    internal_tx_url = make_api_url("account", "txlistinternal", address, startblock=0, endblock=99999999, page=1, offset=10000, sort="asc")
    response2 = get(internal_tx_url)
    data2 = response2.json()["result"]
    
    data.extend(data2)
    data.sort(key=lambda x: int(x['timeStamp']))

    current_balance = 0
    balances = []
    times = []
    wallets = []
    
    for tx in data:
        to = tx["to"]
        from_addr = tx["from"]
        value = int(tx["value"]) / ETHER_VALUE

        if "gasPrice" in tx:
            gas = int(tx["gasUsed"]) * int(tx["gasPrice"]) / ETHER_VALUE
        else:
            gas = int(tx["gasUsed"]) / ETHER_VALUE

        time = datetime.utcfromtimestamp(int(tx['timeStamp']))
        
        # moramo da proverimo da li je transakcija poslata, ili primljena, radi racunanja gas
        if to.lower() == address.lower():
            # dolazaca transakcija
            current_balance += value
            wallets.append(from_addr)
        elif from_addr.lower() == address.lower():
            # poslata transakcija, moramo smanjiti 
            current_balance -= value + gas
            wallets.append(to)
        
        balances.append(current_balance)
        times.append(time)
    
    # uklanjamo duplikate i sortiramo ih po eng alfabetu
    wallets = sorted(list(set(wallets)))
    
    # ispis transakcija u svakom walletu usera
    for w in wallets:
        print(f"Transactions for wallet {w}:")
        for tx in data:
            if tx["from"].lower() == w.lower() or tx["to"].lower() == w.lower():
                direction = "sent" if tx["from"].lower() == w.lower() else "received"
                value = int(tx["value"]) / ETHER_VALUE
                other_wallet = tx["to"] if tx["from"].lower() == w.lower() else tx["from"]
                print(f"{direction} {value:.2f} ETH to/from wallet {other_wallet}")
        print()

    # Grafik balance / time
    plt.plot(times, balances)
    plt.title("Balance over Time")
    plt.xlabel("Time")
    plt.ylabel("Balance (ETH)")
    plt.gcf().autofmt_xdate()
    plt.show()

    

# adresa default korisnika preuzeta sa etherscan sajta
#address = "0xe887312c0595a10ac88e32ebb8e9f660ad9ab7f7"
#alternativno address = input("Enter your Ethereum address: ")
# ispis stanja sa računa korisnika
#print(get_account_balance(address))
# vizuelni pregledan prikaz broja transakcija korisnika druga varijanta
#get_transactions(address)


# jednostavan gui radi lepog i preglednog prikaza i vizuelizacije
def show_balance(address):
    balance = get_account_balance(address)
    balance_window = customtkinter.CTk()
    balance_window.geometry("500x300")
    balance_label = customtkinter.CTkLabel(master=balance_window, text=f"The account balance is {balance} ETH", font=("Roboto",18,'bold'))
    balance_label.pack(pady=50,padx=10)
    balance_window.mainloop()


def fetch_transactions(address):
    get_transactions(address)


def fetch_balance(address):
    show_balance(address)


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")
root = customtkinter.CTk()
root.geometry("1000x400")
frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=20,padx=60,fill="both",expand=True)
label = customtkinter.CTkLabel(master=frame,text="Etherium Fetcher: \n Enter valid address please",font=("Roboto",18,'bold'))
label.pack(pady=12,padx=10)
entry = customtkinter.CTkEntry(master=frame,placeholder_text="Input address here", height=100, width=500,font=("Roboto",18))
entry.pack(pady=12,padx=10)

button1 = customtkinter.CTkButton(master=frame, text="Fetch Transactions", command=lambda: fetch_transactions(entry.get()))
button1.pack(pady=12,padx=10)

button2 = customtkinter.CTkButton(master=frame, text="Show Balance", command=lambda: fetch_balance(entry.get()))
button2.pack(pady=12,padx=10)

root.mainloop()
