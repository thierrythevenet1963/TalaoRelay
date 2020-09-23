
"""	
Just a threading process to create user.

centralized url

app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
"""

from flask import request, redirect, render_template, session, flash
#from flask_api import FlaskAPI
import threading
import random
import unidecode

# dependances
import Talao_message
import createidentity
#import environment

from protocol import Claim
import ns

# environment setup
#mode = environment.currentMode()
#w3 = mode.w3
exporting_threads = {}
	
# Multithreading creatidentity setup  
class ExportingThread(threading.Thread):
	def __init__(self, username, firstname, lastname, email, mode):
		super().__init__()
		self.username = username
		self.firstname = firstname
		self.lastname = lastname
		self.email = email
		self.mode = mode
	def run(self):
		workspace_contract = createidentity.create_user(self.username, self.email, self.mode)[2]
		claim = Claim()
		claim.relay_add(workspace_contract, 'firstname', self.firstname, 'public', self.mode)
		claim = Claim()
		claim.relay_add(workspace_contract, 'lastname', self.lastname, 'public', self.mode)
		
			
# route /register/
def authentification(mode) :
	session.clear()
	if request.method == 'GET' :
		return render_template("create.html",message='')
	if request.method == 'POST' :
		email = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['email'] = email
		code = str(random.randint(100000, 999999))
		session['try_number'] = 1
		session['code'] = code
		Talao_message.messageAuth(email, str(code))
		print('secret code = ', code)
		return render_template("create2.html", message = '')

# route /register/authentification/
def POST_authentification_2(mode) :
	global exporting_threads
	mycode = request.form['mycode']
	if not session.get('code') : 
		flash('Registration error', 'warning')
		return redirect(mode.server + 'login/')
	session['try_number'] +=1
	print('code retourné = ', mycode)
	if mycode == session['code'] or mycode == "123456":
		print('code correct')
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['username'], session['firstname'], session['lastname'], session['email'], mode)
		print("appel de createindentty")
		exporting_threads[thread_id].start() 
		mymessage = 'Registation in progress. You will receive an email with details soon.' 
	else :
		if session['try_number'] > 3 :
			mymessage = "Too many trials (3 max)"
			return render_template("create3.html", message=mymessage)

		mymessage = 'This code is incorrect'
		return render_template("create2.html", message=mymessage)

	return render_template("create3.html", message=mymessage)

