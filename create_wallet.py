import requests
import time
from eth_account import Account
from eth_account.messages import encode_defunct
from hexbytes import HexBytes
from typing import Optional

# Your public key generated in the previous step
signer_public_key = "0x04f2b6c504fb131ff85e24c59f55e513d4e31135b7722f4f4c38a3a3a84568856fcf94a4ab5b642e9f8ef5d82bbb87209fc16438daa3dde687d7a1b0316147c5af"

signer_private_key = "0x951962f766bb72155fa64b84fff86cf10c5aaf81164935ebd0f5f8764da1c278"

# Your wallet address generated in the previous step
wallet_address = "0x7E86aC47382Ced410d6EFd6d542E6fB656feE58F"

# Enter desired destination address
to_address = "0x23B125467AE38C20dAE8A2B52D3019a06A48105c"

# Crossmint's API key
api_key = "sk_staging_5N4wkXQh3LJmTNhioALC1teikFkCJTMTac9f34ntoHf3dDFTUmG6vFyjbRGrr6y3g75j6GsUafurTGsrnbqg7w8ihYFPuPCfGWpYtDtcsHCTaARb3KKAhjSUQaLB14GFpCpnBbwDxa1RHRott6KaX2DfP2kRzs8FM1ufjPUwptaHjRhoGrZtJH1Q9qMdunHVR9wHhK2hGykmy8gQmRcji5u9"


def create_wallet(signer_public_key, api_key):
    url = "https://staging.crossmint.com/api/v1-alpha2/wallets"

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    data = {
        "type": "evm-smart-wallet",
        "config": {
            "adminSigner": {
                "type": "evm-keypair",
                "address": signer_public_key
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def create_transaction(new_wallet_address, to_address, api_key):
    url = "https://staging.crossmint.com/api/v1-alpha2/wallets/{}/transactions".format(
        new_wallet_address)

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    data = {
        "params": {
            "calls": [{
                "to": to_address,
                "value": "1000000000000000",  # 0.001 ETH in wei
                "data": "0x"
            }],
            "chain":
            "base-sepolia",
            "signer":
            "evm-keypair:{}".format(wallet_address)
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def handle_sign(private_key: str, message: str) -> Optional[str]:
    account = Account.from_key(private_key)
    message_to_sign = encode_defunct(text=message)

    # Sign the message
    signed_message = account.sign_message(message_to_sign)

    # Return the signature as hex string with 0x prefix
    signature_hex = signed_message.signature.hex()
    return "0x{}".format(
        signature_hex) if not signature_hex.startswith('0x') else signature_hex


def submit_approval(new_wallet_address, transaction_id, signer_public_key,
                    signature, api_key):
    response = requests.post(
        "https://staging.crossmint.com/api/v1-alpha2/wallets/{}/transactions/{}/approvals"
        .format(new_wallet_address, transaction_id),
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        },
        json={
            "approvals": [{
                "signer": "evm-keypair:{}".format(wallet_address),
                "signature": signature
            }]
        })
    return response.json()


def check_transaction_status(wallet_address, transaction_id, api_key):
    url = "https://staging.crossmint.com/api/v1-alpha2/wallets/{}/transactions/{}".format(
        wallet_address, transaction_id)

    headers = {"X-API-KEY": api_key}

    response = requests.get(url, headers=headers)
    return response.json()


# wallet_resp = create_wallet(signer_public_key=wallet_address, api_key=api_key)
# print(wallet_resp)

# new_wallet_address = wallet_resp["address"]

# transaction_resp = create_transaction(new_wallet_address=new_wallet_address,
#                                       to_address=to_address,
#                                       api_key=api_key)
# print(transaction_resp)

# message = transaction_resp.get("approvals").get("pending")[0].get("message")
# print(message)

# signature = handle_sign(private_key=signer_private_key, message=message)
# print(signature)

# transaction_id = transaction_resp.get("id")

# result = submit_approval(new_wallet_address, transaction_id, signer_public_key,
#                          signature, api_key)
# print(result)

new_wallet_address = "0x62Aae5c9e1e1C5B68572E113eA557BB122170eb6"
transaction_id = "a5ef425d-66f2-4faa-b3cb-bccc54eab666"

# Poll until the transaction is complete
while True:
    transaction = check_transaction_status(new_wallet_address, transaction_id,
                                           api_key)
    # print(transaction)
    if transaction["status"] in ["success", "failed"]:
        print("Transaction {transaction['status']}")
        break
    print("Transaction pending, waiting...")
    time.sleep(5)  # Wait 5 seconds before checking again
