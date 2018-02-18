from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Leagues, Teams, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Database connection and session creation
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a new user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Get the users information
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Get the user's id
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Set up the Google login connection route
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain the authorization code
    code = request.data

    try:
        # Upgrade authorization code into credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check access token validity
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If error, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token is for intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token is valid for app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token client ID does not match app client ID."), 401)
        print "Token client ID does not match app client ID."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already'
                                            'connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store access token in the session.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user's info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists, if not, make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
    	user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Hello, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"'
    output += ' "border-radius: 150px;-webkit-border-radius: 150px;"'
    output += ' "-moz-border-radius: 150px;"> '
    flash("you have logged in as %s" % login_session['username'])
    print "Complete!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is blank'
        response = make_response(json.dumps('Current user'
                                            'not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'Gdisconnect access token is %s', access_token
    print 'The user name is: '
    print login_session['username']
    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s'
        % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('You have successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for'
                                            'given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all leagues
@app.route('/')
@app.route('/leagues')
def showLeagues():
    leagues = session.query(Leagues).all()
    if 'username' not in login_session:
        return render_template('publicleagues.html', leagues=leagues)
    else:
        return render_template('leagues.html', leagues=leagues)

# JSON format for leagues
@app.route('/leagues/JSON')
def leaguesJSON():
    leagues = session.query(Leagues).all()
    return jsonify(Leagues=[i.serialize for i in leagues])

#Create a new league
@app.route('/leagues/new', methods=['GET', 'POST'])
def newLeague():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newLeague = Leagues(title=request.form['name'],
                                  description=request.form['description'],
                                  user_id=login_session['user_id'])
        session.add(newLeague)
        session.commit()
        return redirect(url_for('showLeagues'))
    else:
        return render_template('newleague.html')


#Edit a league
@app.route('/leagues/<int:league_id>/edit', methods=['GET', 'POST'])
def editLeague(league_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedLeague = session.query(Leagues).filter_by(id=league_id).one()
    if editedLeague.user_id != login_session['user_id']:
        return "<script>function myFunction() \
                {alert('You are not authorized to edit this league. \
                Please create your own league in order to edit.');} \
                </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedLeague.title = request.form['name']
        if request.form['description']:
            editedLeague.description = request.form['description']
        session.add(editedLeague)
        session.commit()
        return redirect(url_for('showLeagues'))
    else:
        return render_template(
            'editleague.html',
            league_id=league_id,
            league=editedLeague)


#Delete a league
@app.route('/leagues/<int:league_id>/delete', methods=['GET', 'POST'])
def deleteLeague(league_id):
    if 'username' not in login_session:
        return redirect('/login')
    leagueToDelete = session.query(Leagues).filter_by(id=league_id).one()
    teamsListToDelete = session.query(Teams).filter_by(league_id=league_id).all()
    if leagueToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
               to delete this league. Please create your own league in \
               order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        for i in teamsListToDelete:
            session.delete(i)
            session.commit()
        session.delete(leagueToDelete)
        session.commit()
        return redirect(url_for('showLeagues'))
    else:
        return render_template(
            'deleteleague.html',
            league=leagueToDelete, league_id=league_id)


#Show a league team
@app.route('/leagues/<int:league_id>/teams')
def showTeams(league_id):
    league = session.query(Leagues).filter_by(id=league_id).one()
    creator = getUserInfo(league.user_id)
    teamsList = session.query(Teams).filter_by(league_id=league_id)
    if 'username' not in login_session \
            or creator.id != login_session['user_id']:
        return render_template(
            'publicteams.html', teamsList=teamsList,
            league=league, creator=creator, league_id=league_id)
    else:
        return render_template(
            'teams.html', league=league, teamsList=teamsList,
            creator=creator, league_id=league_id)


# Show league teams in JSON format 
@app.route('/leagues/<int:league_id>/teamsList/JSON')
def teamsJSON(league_id):
    league = session.query(Leagues).filter_by(id=league_id).one()
    teamsList = session.query(Teams).filter_by(league_id=league_id)
    return jsonify(Teams=[i.serialize for i in teamsList])


# Create a new league team
@app.route('/leagues/<int:league_id>/teamsList/new', methods=['GET', 'POST'])
def newTeam(league_id):
    if 'username' not in login_session:
        return redirect('/login')
    league = session.query(Leagues).filter_by(id=league_id).one()
    teamsList = session.query(Teams).filter_by(league_id=league_id)
    if request.method == 'POST':
        newTeam = Teams(
            title=request.form['name'],
            description=request.form['description'],
            league_id=league_id, user_id=login_session['user_id'])
        session.add(newTeam)
        session.commit()
        return redirect(url_for(
            'showTeams', league=league,
            teamsList=teamsList, league_id=league_id))
    else:
        return render_template(
            'newteam.html', league_id=league_id,
            league=league)


# Edit a league team
@app.route('/teamsList/<int:teamsList_id>/edit', methods=['GET', 'POST'])
def editTeams(teamsList_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedTeamsList = session.query(Teams).filter_by(id=teamsList_id).one()
    if editedTeamsList.user_id != login_session['user_id']:
		return "<script>function myFunction() \
        {alert('You are not authorized to edit this team. \
         Please create your own team in order to edit.');}\
         </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedTeamsList.title = request.form['name']
        if request.form['description']:
            editedTeamsList.description = request.form['description']
        session.add(editedTeamsList)
        session.commit()
        return redirect(url_for('showTeams',
                                league_id=editedTeamsList.league_id))
    else:
        return render_template(
            'editteamslist.html',
            league_id=editedTeamsList.league_id,
            teamsList_id=teamsList_id, teamsList=editedTeamsList)


# Delete a league team
@app.route('/teamsList/<int:teamsList_id>/delete', methods=['GET', 'POST'])
def deleteTeams(teamsList_id):
    if 'username' not in login_session:
        return redirect('/login')
    teamsListToDelete = session.query(Teams).filter_by(id=teamsList_id).one()
    if teamsListToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() \
        {alert('You are not authorized to edit this teamsList. \
         Please create your own teamsList in order to edit.');} \
         </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(teamsListToDelete)
        session.commit()
        return redirect(url_for(
            'showTeams',
            league_id=teamsListToDelete.league_id))
    else:
        return render_template(
            'deleteteamslist.html', teamsList=teamsListToDelete,
            teamsList_id=teamsListToDelete.id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)