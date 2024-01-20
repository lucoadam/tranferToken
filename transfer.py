from web3 import Web3
import csv
import math

configs = {
    'token_address': '0x7B0cfD32D9596932993133703cd0723ea027d3ce',
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

token_abi = [
    {
        'constant': False,
        'inputs': [{'name': 'recipient', 'type': 'address'}, {'name': 'amount', 'type': 'uint256'}],
        'name': 'transfer',
        'outputs': [{'name': '', 'type': 'bool'}],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'decimals',
        'outputs': [{'name': '', 'type': 'uint8'}],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function'
    }
]

token_contract = w3.eth.contract(address=configs['token_address'], abi=token_abi)

failed = []

def send_tokens():
    decimals = token_contract.functions.decimals().call()
    multiplier = math.pow(10, decimals)

    for wall in wallets:
        try:
            # Ensure the address is checksummed
            recipient_address = Web3.to_checksum_address(wall['address'])
            print("Index: ", wallets.index(wall),f"Sending {wall['amount']} tokens to {recipient_address}")

            # Convert amount to the smallest unit based on the token's decimals
            amount_in_token_units = float(wall['amount']) * (10 ** decimals)
            amount_in_wei = int(amount_in_token_units)
            tx = {
                'from': str(wallet.address),
                'gas': 200000,  # Set gas limit; adjust based on your needs
                # 'gasPrice': w3.toWei('10', 'gwei')  # Optional: Uncomment and adjust if you want to specify gasPrice
            }
            tx = token_contract.functions.transfer(recipient_address, amount_in_wei).build_transaction({
                'chainId': w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': w3.to_wei('10', 'gwei'),
                'nonce': w3.eth.get_transaction_count(wallet.address),
                'from': wallet.address,
            })
            signed_tx = w3.eth.account.sign_transaction(tx, configs['private_key'])
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
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


send_tokens()
