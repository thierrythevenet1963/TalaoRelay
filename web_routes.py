

"""
External routes for Oauth clients
flow available :
'password'
    curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:3000/api/v1/oauth/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile
    curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:3000/api/v1/api/me

'client_credentials' Celui que l on utilise
    curl -u pyD3s4TGQL6j1B4w1Dz522g3:6elzYVTLDxbBUKUIKdPT2FZ6keOf8zTqGO2RrnuBfTSDPElY -XPOST http://127.0.0.1:5000/api/v1/oauth/token -F grant_type=client_credentials -F scope=profile

    curl -H "Authorization: Bearer jPEFgk8tuql278BEi0tHqGD3sMmVbJTi2Cj7EbuKtB" http://127.0.0.1:5000/api/v1/api/me

'authorization_code' : celui de France Connect (avec en plus OpenId option)
    open http://127.0.0.1:3000/api/v1/oauth/authorize?response_type=code&client_id=${client_id}&scope=profile
    After granting the authorization, you should be redirected to `${redirect_uri}/?code=${code}`

    curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:5000/oauth/token -F grant_type=authorization_code -F scope=profile -F code=${code}

    curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:3000/api/v1/api/me
"""




import os
import time
from flask import request, session, url_for, Response, abort, flash
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token, client_authenticated
from authlib.oauth2 import OAuth2Error
from models import db, User, OAuth2Client
from oauth2 import authorization, require_oauth
import json
import ns
import environment
import constante
from protocol import read_profil

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
mode = environment.currentMode(mychain,myenv)


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if session.get('username') is None :
		abort(403)
	else :
		return session['username']

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


#@bp.route('/api/v1', methods=('GET', 'POST'))
def home():
    check_login()
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        # if user is not just to log in, but need to head back to the auth page, then go for it
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/api/v1')
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    return render_template('/oauth/home.html', user=user, clients=clients)


#@bp.route('/api/v1/oauth_logout')
def oauth_logout():
    check_login()
    del session['id']
    return redirect('/user')

""" login pour les utilisateurs qui viennent d'une application cliente par OAuth2
Le login doit etre de type two factor

"""
#@bp.route('/api/v1/oauth_login')
def oauth_login():
    if request.method == 'GET' :
        session['url'] = request.args.get('next')
        return render_template('/oauth/oauth_login.html')
    if request.method  == 'POST' :
        url = session['url']
        username = request.form.get('username')
        if not ns.username_exist(username, mode)  :
            flash('Username not found', "warning")
            return redirect(url)
        if not ns.check_password(username, request.form['password'].lower(), mode)  :
            flash('Wrong password', "warning")
            return redirect(url)
        # if secret code wrong redirect to url
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        print('User logged in Talao.co')
        session['username']=username
    return redirect(url)


#@bp.route('/api/v1/create_client', methods=('GET', 'POST'))
""" gestion des grant client 
"""
def create_client():
    check_login()
    user = current_user()
    if not user:
        return redirect('/api/v1')
    if request.method == 'GET':
        return render_template('/oauth/create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )
    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)
    db.session.add(client)
    db.session.commit()
    return redirect('/api/v1')

#@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    check_login()
    return authorization.create_endpoint_response('revocation')

#@bp.route('/api/v1/oauth/token', methods=['POST'])
def issue_token():
    response = authorization.create_token_response()
    print(response)
    return response




# AUTHORIZATION CODE endpoint
#@bp.route('/api/v1/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('oauth_login', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('/oauth/authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form.get('confirm') == 'on' :
       
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


#@bp.route('/api/v1/oauth/authorize_extended', methods=['GET', 'POST'])
def authorize_extended():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('oauth_login', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('/oauth/authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form.get('confirm') == 'on' :
        grant_user = user
        # ajouter une demande de partnership faite au client
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)





#  CLIENT CREDENTIALS Endpoint

#@bp.route('/api/v1/oauth_resume')
@require_oauth('resume')
def oauth_resume():
    client_id = current_token.client_id
    #print('current token =', current_token.__dict__)
    #print('client id =', client_id)
    client = OAuth2Client.query.filter_by(client_id=client_id).first().__dict__
    user_id = current_token.user_id
    user = User.query.get(user_id)
    #print ('client  metadata = ', client['_client_metadata'])

    #json_data = request.__dict__.get('data').decode("utf-8")
    #dict_data = json.loads(json_data)
    #print('data recu dans routes.py = ', json_data)
    username = user.username
    if username is None :
        workspace_contract = None
        print('something is wrong in userinfo')
        content=json.dumps({"msg" : "invalid username"}) # content est un json
        response = Response(content, status=401, mimetype='application/json')
        return response
    workspace_contract = ns.get_data_from_username(username, mode)['workspace_contract']
    user_info = dict()
    profile = read_profil(workspace_contract, mode, 'full')[0]
    user_info['sub'] = 'did:talao:' + mode.BLOCKCHAIN +':' + workspace_contract[2:]
    user_info['given_name'] = profile.get('firstname')
    user_info['family_name'] = profile.get('lastname')
    user_info['gender'] = profile.get('gender')
    user_info['email']= profile.get('contact_email') if profile.get('contact_email') != 'private' else None
    user_info['birthdate'] = profile.get('birthdate') if profile.get('birthdate') != 'private' else None
    # preparation de la reponse
    content = json.dumps(user_info)
    response = Response(content, status=200, mimetype='application/json')
    return response


#@bp.route('/api/v1/oauth_identity')
@require_oauth('identity')
def oauth_identity():
    print('current token =', current_token.__dict__)
    client_id = current_token.client_id
    client = OAuth2Client.query.filter_by(client_id=client_id).first().__dict__
    user_id = current_token.user_id
    user = User.query.get(user_id)
    json_data = request.__dict__.get('data').decode("utf-8")
    dict_data = json.loads(json_data)
    print('data reçue = ',dict_data)
    # preparation de la reponse
    data= {"msg" : 'ok'}
    content = json.dumps(data)
    response = Response(content, status=200, mimetype='application/json')
    return response

""" exempled d'un client

import requests
import json
import shutil


def send_dict() :
	headers = {'Content-Type': 'application/json',
				'Authorization': 'Bearer  K2jJkgpWFFS3PNXHbWLpyE2m7DcX9GejxEuDjhMExP'}
	data = {'name' : 'pierre', 'data' : 125}
	response = requests.post('http://127.0.0.1:3000/api/v1/api/me', data=json.dumps(data), headers=headers)
	return response.json()

print(send_dict())
"""