
from datetime import datetime
import environment
import sqlite3
import unidecode

import constante

mode = environment.currentMode()
path = mode.db_path

def _contractsToOwners(workspace_contract, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	return address

def _ownersToContracts(address, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	return workspace_address
	
	
def _init_nameservice():
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	cur.execute('create table alias(alias_name text, identity_name text, email text, date real)')
	
	cur.execute('create table resolver(identity_name text, identity_workspace_contract text, date real)')
	
	cur.execute('create table publickey(address text, key text)')
	conn.commit()
	cur.close()
	return
	
def init_host(host_name) :
	""" This function is only used in createcompany """
	conn = sqlite3.connect(path + host_name + '.db')
	cur = conn.cursor()
	cur.execute('create table manager(manager_name text, identity_name text, email text, date real)')
	conn.commit()
	cur.close()

def setup() :
	
	_init_nameservice()
	
	init_host('talao')
	init_host('thales')
	init_host('skillvalue')
	init_host('relay')
	init_host('bnp')
	
	add_identity('talao', '0xfafDe7ae75c25d32ec064B804F9D83F24aB14341', 'contact@talao.io',mode)
	add_identity('bnp', '0x4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4', 'contact@bnp.talao.io', mode)
	add_identity('skillvalue', '0xbF14A0F4DC31c93545CBE210fb24f2a1fc6Bb208', 'contact@skillvalue.talao.io', mode)
	add_identity('thales', '0x9A662a74F44B7fe61b69b0AFbfE73B8AbF38EE46', 'contact@thales.talao.io', mode)
	add_identity('pascalet', '0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF', 'pascalet@gmail.talao.io',mode)
	add_identity('jean', '0x0271c88C648D6F44B83f8CEcFFc8A85C390e9C21', 'jean@gmail.talao.io', mode)
	add_identity('relay', '0xD6679Be1FeDD66e9313b9358D89E521325e37683', 'contact@relay.talao.io', mode)	
	
	
	add_alias('jeanpascalet', 'pascalet', 'jeanpascalet@gmail.talao.io')
	add_alias('jp2', 'pascalet', 'jp@gmail.talao.io')
	add_alias('jp1', 'pascalet', 'jp@gmail.talao.io')

	add_manager('jp', 'pascalet', 'bnp', 'jp@bnp.talao.io')
	add_manager('jp1', 'pascalet', 'bnp', 'jp@bnp.talao.io')
	add_manager('jp2', 'pascalet', 'bnp', 'jp@bnp.talao.io')
	
def build_username(firstname, lastname) :
	_firstname = firstname.lower()
	_lastname = lastname.lower()
	_username = unidecode.unidecode(_firstname) + unidecode.unidecode(_lastname)
	username = _username.replace(" ", "")
	if get_data_from_username(username, mode) is not None  :
		username = username + str(random.randint(1, 100))
	return username



def add_identity(identity_name, identity_workspace_contract, email, mode) :
	""" This is called once (first time), it creates a username for an identity and it creates an alias with same username as alias name. Publickey is created too"""
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()	
	
	data = {'identity_name' : identity_name, 'identity_workspace_contract' : identity_workspace_contract, 'date' : datetime.timestamp(now)} 
	c.execute("INSERT INTO resolver VALUES (:identity_name, :identity_workspace_contract, :date)", data)
	
	data = {'alias_name' : identity_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now)} 
	c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date )", data)
	
	address = _contractsToOwners(identity_workspace_contract, mode)
	key = mode.w3.solidityKeccak(['address'], [address]).hex()
	
	data = {'address' : address, 'key' : key}
	c.execute("INSERT INTO publickey VALUES (:address, :key)", data)

	conn.commit()
	conn.close()
	return

	
def add_alias(alias_name, identity_name, email) :
	
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'alias_name' : alias_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now)} 
	c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date )", data)
	conn.commit()
	conn.close()
	return		


def does_alias_exist(alias_name) :
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'alias_name' : alias_name} 
	c.execute("SELECT identity_name FROM alias WHERE alias_name = :alias_name " , data)
	select = c.fetchall()
	conn.commit()
	conn.close()
	if select == [] :
		return False
	else :
		return True

def remove_alias(alias_name) :
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'alias_name' : alias_name} 
	try :
		c.execute("DELETE FROM alias WHERE alias_name = :alias_name " , data)
		execution  = True
	except sqlite3.OperationalError :
		execution = False
	conn.commit()
	conn.close()
	return execution
	
def add_manager(manager_name, identity_name, host_name, email) :	
	""" jean.bnp : jean = manager_name , bnp = host_name """
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'manager_name' : manager_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now)} 
	c.execute("INSERT INTO manager VALUES (:manager_name, :identity_name, :email, :date )", data)
	conn.commit()
	conn.close()
	return		

def does_manager_exist(manager_name, host_name) :
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'manager_name' : manager_name} 
	c.execute("SELECT identity_name FROM manager WHERE manager_name = :manager_name " , data)
	select = c.fetchall()
	conn.commit()
	conn.close()
	if select == [] :
		return False
	else :
		return True

def remove_manager(manager_name, host_name) :
	conn = sqlite3.connect(path + host_name + '.db')
	c = conn.cursor()
	data = {'manager_name' : manager_name} 
	try : 
		c.execute("DELETE FROM manager WHERE manager_name = :manager_name " , data)
		execution  = True
	except sqlite3.OperationalError :
		execution = False
	conn.commit()
	conn.close()
	return execution


def _get_data(username) :
	manager_name,s,host_name = username.rpartition('.')
	# it is not a manager
	if manager_name == '' :
		conn = sqlite3.connect(path + 'nameservice.db')
		c = conn.cursor()
		data ={'username' : username}
		c.execute("SELECT identity_name, email FROM alias WHERE alias_name = :username " , data)
		select = c.fetchone()
		if select is None : 
			print('ici')
			conn.commit()
			conn.close()
			print(username + ' n existe pas dans la table des alias de nameservice')
			return None 
			
		(identity_name, alias_email) = select
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			print('l alias ' + username + ' n a pas d identity dans le resolver')
			return None 
		identity_workspace_contract = select[0]
		conn.commit()
		conn.close()
		return identity_workspace_contract, None, alias_email
	else :
		conn = sqlite3.connect(path + host_name + '.db')
		c = conn.cursor()
		data ={'manager_name' : manager_name}
		
		try :
			c.execute("SELECT identity_name, email FROM manager WHERE manager_name = :manager_name " , data)
		except sqlite3.OperationalError :
			print('la database ' + host_name + ' n existe pas')
			return None	
		
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			print('le manager name : '+ manager_name + ' n existe pas dans la table locale de '+ host_name)
			return None 
		
		(identity_name, manager_email) = select
		conn.commit()
		conn.close()
		
		conn = sqlite3.connect(path + 'nameservice.db')
		c = conn.cursor()
		
		data ={'host_name' : host_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :host_name " , data)
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			print(' le host n existe pas das le resolver')
			return None 
		host_workspace_contract = select[0]
		
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		identity_workspace_contract = c.fetchone()[0]

		conn.commit()
		conn.close()
		return identity_workspace_contract, host_workspace_contract, manager_email

		
def get_username_from_resolver(workspace_contract) :
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'identity_workspace_contract' : workspace_contract} 
	c.execute("SELECT identity_name FROM resolver WHERE identity_workspace_contract = :identity_workspace_contract " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]	

def get_address_from_publickey(publickey) :
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'key' : publickey} 
	c.execute("SELECT address FROM publickey WHERE key = :key " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]		

def get_data_from_publickey(publickey, mode) :
	""" username comes from resolver"""
	address = get_address_from_publickey(publickey)
	print('address =', address)
	if address is None :
		return None
	workspace_contract = _ownersToContracts(address,mode)
	print('workspace_contract = ', workspace_contract)
	username = get_username_from_resolver(workspace_contract)
	print('username =', username)
	if username is None :
		return None
	return {'address' : address,
			'workspace_contract' : workspace_contract,
			'username' : username}


def get_data_for_login(username) :
	call = _get_data(username)
	if call is None :
		return None
	identity, host, email = call
	if host is None :
		return identity, email
	else :
		return host, email 

def get_data_from_username(username, mode) :
	""" It is almost the same as get_data_for_login but with dict as return """
	call = get_data_for_login(username)
	if call is None :
		return None
	workspace_contract, email = call
	address = _contractsToOwners(workspace_contract,mode)
	return {'email' : email,
			'address' : address,
			'workspace_contract' : workspace_contract,
			'username' : username}

def get_alias_list(workspace_contract) :
	call = get_username_from_resolver(workspace_contract)
	if call is None :
		return []
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	identity_name = call	
	data ={'identity_name' : identity_name}
	c.execute("SELECT alias_name, email FROM alias WHERE identity_name = :identity_name " , data)
	select = c.fetchall()
	alias = list()
	for row in select :
		alias.append({'username' : row[0], 'email' : row[1]})	
	return alias

def get_username_list_from_email(email) :
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data ={'email' : email}
	c.execute("SELECT identity_name FROM alias WHERE email = :email" , data)
	select = c.fetchall()
	username_list = list()
	for row in select :
		username_list.append(row[0])	
	return username_list

def get_manager_list(workspace_contract) :
	call = get_username_from_resolver(workspace_contract)
	if call is None :
		return []
	host_name = call
	conn = sqlite3.connect(path + host_name + '.db')
	c = conn.cursor()
	identity_name = call	
	data ={'identity_name' : identity_name}
	try :
		c.execute("SELECT manager_name, email FROM manager " , data)
	except sqlite3.OperationalError :
		print('la database ' + host_name + ' n existe pas')
		return []	
	select = c.fetchall()
	alias = list()
	for row in select :
		alias.append({'username' : row[0]+'.' + host_name, 'email' : row[1]})	
	return alias
	
if __name__ == '__main__':

	# environment setup
	mode = environment.currentMode()
	w3 = mode.w3

	#setup()
	
	print(get_data_from_username('pascalet', mode))