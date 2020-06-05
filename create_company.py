"""
Toutes les company sont crées par Talao et signées par Talao

les company ne sont pas enregistrées dans le backend de l issuer

un cle de type 1 et crée pour Talao qui signe les transactions initiales.


"""


import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import http.client
import json
from datetime import datetime
import ipfshttpclient
from eth_account.messages import encode_defunct


# dependances
from protocol import ether_transfer, ownersToContracts, token_transfer, createVaultAccess, addkey, addName
import Talao_ipfs
import constante
import environment


# initialisation de l'environnement
mode=environment.currentMode()
w3=mode.w3

# variable pour calcul RSA
password = mode.password
master_key = ""
salt = ""



def _createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :

	contract=w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.createWorkspace(2001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)	
	return hash

# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)


def _creationworkspacefromscratch(email): 
""" l email est crypté """

	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	eth_a=account.address
	eth_p=account.privateKey.hex()
	print('adresse = ',eth_a)
	print('private key = ', eth_p)
	
	# création de la cle RSA (bytes) deterministic
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
	global salt
	global master_key
	salt = eth_p
	master_key = PBKDF2(password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(eth_a)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier=open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# création de la cle AES
	AES_key = get_random_bytes(16)	

	# création du Secret
	SECRET_key = get_random_bytes(16)
	SECRET=SECRET_key.hex()
	print('SECRET = ', SECRET)
	
	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
	# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
	# Email encrypted with RSA Key
	bemail = bytes(email , 'utf-8')	
	email_encrypted = cipher_ras.encrypt(bemail)
	print('email encrypted =' ,email_encrypted)
	
	# Transaction pour le transfert de 0.06 ethers depuis le portfeuille TalaoGen
	hash1=ether_transfer(eth_a, 60,mode)
	print('hash de transfert de 0.06 eth = ',hash1)
	
	# Transaction pour le transfert de 101 tokens Talao depuis le portfeuille TalaoGen
	hash2=token_transfer(eth_a,101,mode)
	print('hash de transfert de 100 TALAO = ', hash2)
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=createVaultAccess(eth_a,eth_p,mode)
	print('hash du createVaultaccess = ', hash3)
	
	# Transaction pour la creation du workspace :
	bemail = bytes(email , 'utf-8')	
	hash4 =_createWorkspace(eth_a,eth_p,RSA_public, AES_encrypted, SECRET_encrypted, email_encrypted, mode)
	print('hash de createWorkspace =', hash4)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_address = ownersToContracts(eth_a,mode)
	print( 'workspace contract = ', workspace_contract_address)
		
	return eth_a, eth_p, SECRET, workspace_contract_address, email, SECRET, AES_key


##############################################################
#             MAIN
##############################################################
# tous les claims sont signe par Talao qui cré les companies

# Ouverture du fichier d'archive Talao_Identity.csv
fname= mode.BLOCKCHAIN +"_Talao_Identity.csv"
identityfile = open(fname, "a")
writer = csv.writer(identityfile)

# setup
email = ""
username = ""

if username_to_data(username, mode) is not None :
	print('username already used')
	sys.exit(0)
	 
# calcul du temps de process
time_debut=datetime.now()

# CREATION DU WORKSPACE MINIMUM
email = company['profil']["contact"]['email'] # base pour la construction du registre de nameservice
(address, private_key,password, workspace_contract, email, SECRET, AES_key)=_creationworkspacefromscratch(email)

# management key (1) issued to Web Relay (agent)
addkey(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 



# update Register
addName(username, address, workspace_contract, email, mode)

# calcul de la duree de transaction et du cout
time_fin=datetime.now()
time_delta=time_fin-time_debut
print('Durée des transactions = ', time_delta)
a=w3.eth.getBalance(address)
cost=0.06-a/1000000000000000000	
print('Cout des transactions =', cost)	


# mise a jour du fichier archive Talao_Identity.csv
status="Compnay Identity createcompany.py"
writer.writerow(( datetime.today(), username, "", email, status, address, private_key, workspace_contract, "", email, SECRET, AES_key,cost) )

# fermeture des fichiers
identityfile.close()
sys.exit(0)