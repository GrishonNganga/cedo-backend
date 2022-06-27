import json, requests
from re import A
from web3 import Web3

network_url= "https://alfajores-forno.celo-testnet.org"
web3 = Web3(Web3.HTTPProvider(network_url))
contract_address = "0xBE390eD3917bb9703c474ce2f64a3D6a00C5e46e"
cUSD_contract_address = "0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"

master_key = "0x21a91CE4F46b5D55c561E84d18FECd483A9a0E5c"
master_pass = "3777e17285dfca20bf969828205e26621c6ec1429f51a084190ee61e09b2a5e8"

contract_abi = json.loads('''[
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_user",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_campaign",
				"type": "address"
			}
		],
		"name": "checkIfUserParticipatedInCampaign",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_id",
				"type": "address"
			}
		],
		"name": "createNewCampaign",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_userAddress",
				"type": "address"
			}
		],
		"name": "createNewUser",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_campaignAddress",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "fundCampaign",
		"outputs": [],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_campaignAddress",
				"type": "address"
			}
		],
		"name": "getCampaignAddress",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_campaignAddress",
				"type": "address"
			}
		],
		"name": "getCampaignPayouts",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_campaignAddress",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_userAddress",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "payout",
		"outputs": [],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "totalCampaigns",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "totalUsers",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]''')

cUSD_contract_abi = json.loads('''
[
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "owner",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "spender",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Approval",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "from",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "to",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Transfer",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "allowance",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "approve",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "totalSupply",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "transfer",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "transferFrom",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]
''')

cedo_contract = web3.eth.contract(address=contract_address, abi=contract_abi)
cUSD_contract = web3.eth.contract(address=cUSD_contract_address, abi=cUSD_contract_abi)

def create_account(password, amount=None):
	account = web3.eth.account.create()
	account = account.encrypt(password)
	print("ACCCC")
	print(account)
	if amount:
		tx = {'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price,"gas": 2000000, "to": Web3.toChecksumAddress(f'0x{account["address"]}'), "value": int(amount * 1000000000)}
	else:
		tx = {'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price,"gas": 2000000, "to": Web3.toChecksumAddress(f'0x{account["address"]}')}	
	
	signed_tx = web3.eth.account.signTransaction(tx, private_key=master_pass)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])
	
	print("---------Transaction------------")
	print(tx_result)
	if tx_result and tx_result["status"]:
		print("Accccounnnntt created")
		print(account)
		return account
	else:
		return False


def get_balance(public_key):
	return cUSD_contract.functions.balanceOf(Web3.toChecksumAddress(public_key)).call()

def fund_campaign(campaign_address, amount):
	print(cUSD_contract.functions.balanceOf(campaign_address).call())
	print(cUSD_contract.functions.balanceOf(master_key).call())
	tx = cUSD_contract.functions.approve(contract_address, amount).buildTransaction({'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=master_pass)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])

	tx = cedo_contract.functions.fundCampaign(master_key, campaign_address, amount).buildTransaction({'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=master_pass)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])
	if tx_result and  tx_result["status"]:
		return True


def campaign_payout(campaign_address_obj, campaign_pk, user_address, amount):
	user_address = Web3.toChecksumAddress(user_address)
	campaign_address = Web3.toChecksumAddress(f'0x{campaign_address_obj["address"]}')
	campaign_pk = Web3.toHex(web3.eth.account.decrypt(campaign_address_obj, campaign_pk))

	print("----------campaign add-----")
	print(campaign_address)
	print(campaign_pk)

	tx = cUSD_contract.functions.approve(contract_address, amount *1000000000).buildTransaction({'nonce': web3.eth.get_transaction_count(campaign_address), "gasPrice": web3.eth.gas_price})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=campaign_pk)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])

	tx = cedo_contract.functions.payout(campaign_address, user_address, amount).buildTransaction({'nonce': web3.eth.get_transaction_count(campaign_address), "gasPrice": web3.eth.gas_price, "value": amount})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=campaign_pk)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])
	if tx_result and  tx_result["status"]:
		return True
	else: 
		return False

def confirm_participation(user_address, campaign_address):
	return cedo_contract.functions.checkIfUserParticipatedInCampaign(Web3.toChecksumAddress(user_address), Web3.toChecksumAddress(campaign_address)).call()


def create_normal_user(address):
	tx = cedo_contract.functions.createNewUser(address).buildTransaction({'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=master_pass)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])
	if tx_result and  tx_result["status"]:
		return True
	else: 
		return False


def get_accounts_txs(address):
	url = f"https://alfajores-blockscout.celo-testnet.org/api?module=account&action=tokentx&address={address}"
	response = requests.get(url)
	print(response.json())

	return response.json()

# print(create_account("123@Iiht", "100"))

# print(create_account("0x9084eb217c7f996531f960055480c333e43c5bee"))


def add_user_to_blockchain(address):
	tx = cedo_contract.functions.createNewUser(address).buildTransaction({'nonce': web3.eth.get_transaction_count(master_key), "gasPrice": web3.eth.gas_price})
	signed_tx = web3.eth.account.signTransaction(tx, private_key=master_pass)
	web3.eth.send_raw_transaction(signed_tx.rawTransaction)
	tx_result = web3.eth.wait_for_transaction_receipt(signed_tx["hash"])
	if tx_result and  tx_result["status"]:
		return True
	else: 
		return False
