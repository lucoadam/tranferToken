from web3 import Web3
import csv
import math

configs = {
    'private_key': 'private_key',
    'rpc': 'https://data-seed-prebsc-1-s1.binance.org:8545'
}

w3 = Web3(Web3.HTTPProvider(configs['rpc']))
assert w3.is_connected(), "Failed to connect to the Ethereum node."

wallet = w3.eth.account.from_key(configs['private_key'])
w3.eth.defaultAccount = wallet.address

with open('wallets.csv', mode='r') as file:
    reader = csv.reader(file)
    wallets = [{'address': row[0], 'amount': row[1]} for row in reader if row[0] != 'Address']

failed = []

def send_bnb():
    ## check balance is enough
    balance = w3.eth.get_balance(wallet.address)
    print("Balance: ", w3.from_wei(balance, 'ether'))
    amount_to_send = sum([w3.to_wei(float(wall['amount']), 'ether') for wall in wallets])
    print("Amount to send: ", w3.from_wei(amount_to_send, 'ether'))
    gas_price_per_tx = w3.to_wei('10' if w3.eth.chain_id == 0x61 else '3', 'gwei')
    gas_limit_per_tx = 21000
    total_gas_fee = gas_price_per_tx * gas_limit_per_tx * len(wallets)
    print("Total gas fee: ", w3.from_wei(total_gas_fee, 'ether'))
    if balance < amount_to_send + total_gas_fee:
      print("Not enough balance")
      return
    for wall in wallets:
        try:
            # Ensure the address is checksummed
            recipient_address = Web3.to_checksum_address(wall['address'])
            print("Index: ", wallets.index(wall), f"Sending {wall['amount']} BNB to {recipient_address}")

            # Convert amount to Wei
            amount_in_wei = w3.to_wei(float(0.00005), 'ether')

            # Build transaction
            tx = {
                'from': wallet.address,
                'to': recipient_address,
                'value': amount_in_wei,
                'gas': 21000,
                # hex of 97 changed to 0x61
                'gasPrice': w3.to_wei('10' if w3.eth.chain_id == 0x61 else '3', 'gwei'),
                'nonce': w3.eth.get_transaction_count(wallet.address),
            }

            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx, configs['private_key'])
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction hash: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(e)
            failed.append({
                'address': wall['address'],
                'amount': wall['amount']
            })
            break
    with open('failed.csv', mode='w') as file:
        writer = csv.writer(file)
        for wall in failed:
            writer.writerow([wall['address'], wall['amount']])
    print("Done") 

send_bnb()

    
    