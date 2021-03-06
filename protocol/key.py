import logging
logging.basicConfig(level=logging.INFO)

# dependancies
import constante


#######################################################################
# Add key with one purpose
#######################################################################
# @purpose = int, 1,2,3,4, 2002(create doc), 2003(acces to partnership)
#address_from : address which signs
# address_to : key issuer
# address_partner = key receiver

def add_key(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner,purpose,mode, synchronous=True) :

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)

	# keccak (publickey)
	key = w3.soliditySha3(['address'], [address_partner])

	# one checks if key with purpose exists
	key_description = contract.functions.getKey(key).call()
	purpose_list = key_description[0]

	if purpose_list :
		if purpose not in purpose_list :
			# key exists without this purpose, one adds this purpose to the existing key
			txn = contract.functions.addPurpose(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
			signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
			w3.eth.sendRawTransaction(signed_txn.rawTransaction)
			hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
			if synchronous :
				receipt = w3.eth.waitForTransactionReceipt(hash_transaction)
				if not receipt['status'] :
					return False
		else :
			logging.warning("purpose and key already exists")
		return True

	else :
		txn = contract.functions.addKey(key, purpose, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		if synchronous :
			receipt = w3.eth.waitForTransactionReceipt(hash_transaction)
			if not receipt['status'] :
				logging.error('transaction failed . See receipt : %s', receipt)
				return False
		return True


def delete_key(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner, purpose, mode, synchronous=True) :

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)

	key = w3.soliditySha3(['address'], [address_partner])

	# one checks if this key with this purpose exists
	key_description = contract.functions.getKey(key).call()
	purpose_list = key_description[0]
	if purpose not in purpose_list :
		logging.error('this purpose does not exist, cannot delete')
		return False
	else :
		# build, sign and send transaction
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		if synchronous :
			receipt = w3.eth.waitForTransactionReceipt(hash_transaction)
			if not receipt['status'] :
				logging.error('transaction failed . See receipt : %s', receipt)
				return False
		logging.info("delete key done hash = %s", hash_transaction)
		return True

def has_key_purpose(identity_workspace_contract, address_partner, purpose, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = w3.soliditySha3(['address'], [address_partner])
	return contract.functions.keyHasPurpose(key, purpose).call()
