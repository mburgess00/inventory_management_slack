from flask import Flask, request, Response
from slackclient import SlackClient
import os
import json
import sqlite3
import datetime
from prettytable import PrettyTable

sqlite_file = '/opt/ipalers_slack/inventory.sqlite'

application = Flask(__name__)

try:
    slack_slash_token = os.environ['SLACK_TOKEN']
    slack_api_token = os.environ['SLACK_API_TOKEN']
    slack_restricted_channel = os.environ['SLACK_RESTRICTED_CHANNEL']
    print slack_restricted_channel
except KeyError:
    print "slack token not set"

slack_client = SlackClient(slack_api_token)
user_list = slack_client.api_call("users.list", channel=slack_restricted_channel)

def lookup_display_name_by_user(userid):
    data = "Nobody"
    for user in user_list['members']:
        if user['id'] == userid:
	    data = user['profile']['real_name']
    return data

def lookup_id_by_real_name(name):
    data = "Nobody"
    for user in user_list['members']:
        if user['name'] == name:
	    data = user['id']
    return data

@application.route("/equipmentcheckout", methods=['POST'])
def checkout():
    if request.form.get('token') == slack_slash_token:
        api_call = slack_client.api_call("groups.info", channel=slack_restricted_channel)
        if api_call.get('ok'):
            users = api_call['group']['members']
            print users
            calling_user = request.form.get('user_id')
            print calling_user
            if calling_user in users:
		conn = sqlite3.connect(sqlite_file)
		c = conn.cursor()
                text = request.form.get('text')
		item_name = text.split(" ")[0]
		userid = lookup_id_by_real_name(text.split(" ")[1].split('@')[1])
		#sqlstring = 'INSERT INTO items (name,create_date,created_by,custodian) VALUES ("{}","{}","{}","{}");'.format(item_name,datetime.datetime.now(),calling_user,custodian)
		sqlstring = 'SELECT * FROM items WHERE name="{}"'.format(item_name)
		c.execute(sqlstring)
		if c.fetchone()[3] == 1:
		    data = "{} already checked out - please check back in first".format(item_name)
		else:
		    sqlstring = 'INSERT INTO log (user_id,item_name,date,action) VALUES ("{}","{}","{}","{}")'.format(userid,item_name,datetime.datetime.now(),"out")
		    c.execute(sqlstring)
		    sqlstring = 'UPDATE items SET checked_out = "1", checked_out_by = "{}" WHERE name="{}"'.format(userid,item_name)
		    c.execute(sqlstring)
		    conn.commit()
	            c.execute('SELECT * FROM items WHERE name="{}"'.format(item_name))
                    t = PrettyTable(['Item Name','Checked Out To','Custodian'])
                    for row in c:
	                #lookup created_by - row[2]
	                realname = lookup_display_name_by_user(row[2])
	                custodian = lookup_display_name_by_user(row[5])
	                checkedoutto = lookup_display_name_by_user(row[4])
	                t.add_row([row[0],checkedoutto,custodian])

                    data = "```" + t.get_string() + "```"
	        
            else:
                data = "you are not an authorized user"
        return Response(data, status=200)

    return Response("invalid slack token", status=200)

@application.route("/equipmentcheckin", methods=['POST'])
def checkin():
    if request.form.get('token') == slack_slash_token:
        api_call = slack_client.api_call("groups.info", channel=slack_restricted_channel)
        if api_call.get('ok'):
            users = api_call['group']['members']
            print users
            calling_user = request.form.get('user_id')
            print calling_user
            if calling_user in users:
                #put magic code here!
		conn = sqlite3.connect(sqlite_file)
		c = conn.cursor()
                text = request.form.get('text')
		item_name = text.split(" ")[0]
		#sqlstring = 'INSERT INTO items (name,create_date,created_by,custodian) VALUES ("{}","{}","{}","{}");'.format(item_name,datetime.datetime.now(),calling_user,custodian)
		sqlstring = 'SELECT * FROM items WHERE name="{}"'.format(item_name)
		c.execute(sqlstring)
		if c.fetchone()[3] == 0:
		    data = "{} already checked in".format(item_name)
		else:
		    sqlstring = 'INSERT INTO log (item_name,date,action) VALUES ("{}","{}","{}")'.format(item_name,datetime.datetime.now(),"in")
		    c.execute(sqlstring)
		    sqlstring = 'UPDATE items SET checked_out = "0", checked_out_by = "None" WHERE name="{}"'.format(item_name)
		    c.execute(sqlstring)
		    conn.commit()
		    data = "{} checked in".format(item_name)
	            c.execute('SELECT * FROM items WHERE name="{}"'.format(item_name))
                    t = PrettyTable(['Item Name','Checked Out To','Custodian'])
                    for row in c:
	                #lookup created_by - row[2]
	                realname = lookup_display_name_by_user(row[2])
	                custodian = lookup_display_name_by_user(row[5])
	                checkedoutto = lookup_display_name_by_user(row[4])
	                t.add_row([row[0],checkedoutto,custodian])

                    data = "```" + t.get_string() + "```"
            else:
                data = "you are not an authorized user"
        return Response(data, status=200)

    return Response("invalid slack token", status=200)


@application.route("/equipmentlist", methods=['POST'])
def equipmentlist():
    if request.form.get('token') == slack_slash_token:
        #get the equipment here
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	c.execute("SELECT * FROM items")
        t = PrettyTable(['Item Name','Checked Out To','Custodian'])
        for row in c:
	    #lookup created_by - row[2]
	    realname = lookup_display_name_by_user(row[2])
	    custodian = lookup_display_name_by_user(row[5])
	    checkedoutto = lookup_display_name_by_user(row[4])
	    t.add_row([row[0],checkedoutto,custodian])

        data = "```" + t.get_string() + "```"
        return Response(data, status=200)
    return Response("invalid slack token", status=200)

@application.route("/equipmentadd", methods=['POST'])
def equipmentadd():
    print request.form.get('token')
    if request.form.get('token') == slack_slash_token:
        print slack_restricted_channel
        api_call = slack_client.api_call("groups.info", channel=slack_restricted_channel)
        if api_call.get('ok'):
            users = api_call['group']['members']
            print users
            calling_user = request.form.get('user_id')
            print calling_user
            if calling_user in users:
                #put magic code here!
		conn = sqlite3.connect(sqlite_file)
		c = conn.cursor()
                text = request.form.get('text')
		item_name = text.split(" ")[0]
		try:
		    custodian = lookup_id_by_real_name(text.split(" ")[1].split('@')[1])
		except: 
		    custodian = request.form.get('user_id')
		try:
		    sqlstring = 'INSERT INTO items (name,create_date,created_by,custodian,checked_out) VALUES ("{}","{}","{}","{}","0");'.format(item_name,datetime.datetime.now(),calling_user,custodian)
		    c.execute(sqlstring)
		    conn.commit()
	            c.execute('SELECT * FROM items WHERE name="{}"'.format(item_name))
                    t = PrettyTable(['Item Name','Checked Out To','Custodian'])
                    for row in c:
	                #lookup created_by - row[2]
	                realname = lookup_display_name_by_user(row[2])
	                custodian = lookup_display_name_by_user(row[5])
	                checkedoutto = lookup_display_name_by_user(row[4])
	                t.add_row([row[0],checkedoutto,custodian])

                    data = "```" + t.get_string() + "```"
                except sqlite3.IntegrityError:
                    data = "{} already exists".format(item_name,)
            else:
                data = "you are not an authorized user"
        return Response(data, status=200)

    return Response("invalid slack token", status=200)

@application.route("/equipmentupdate", methods=['POST'])
def equipmentupdate():
    print request.form.get('token')
    if request.form.get('token') == slack_slash_token:
        print slack_restricted_channel
        api_call = slack_client.api_call("groups.info", channel=slack_restricted_channel)
        if api_call.get('ok'):
            users = api_call['group']['members']
            print users
            calling_user = request.form.get('user_id')
            print calling_user
            if calling_user in users:
                #put magic code here!
		conn = sqlite3.connect(sqlite_file)
		c = conn.cursor()
                text = request.form.get('text')
		item_name = text.split(" ")[0]
		custodian = lookup_id_by_real_name(text.split(" ")[1].split('@')[1])
		sqlstring = 'UPDATE items SET custodian="{}" WHERE name="{}"'.format(custodian,item_name)
		c.execute(sqlstring)
		conn.commit()
		data = "{} updated to {}".format(item_name, custodian)
            else:
                data = "you are not an authorized user"
        return Response(data, status=200)

    return Response("invalid slack token", status=200)
    
@application.route("/test", methods=['POST'])
def test():
    if request.form.get('token') == slack_slash_token:
	 data = request.form.get('text').split('@')[1] + " = " + lookup_id_by_real_name(request.form.get('text').split('@')[1])
         return Response(data, status=200)
	
@application.route("/userlist", methods=['POST'])
def userlist():
    if request.form.get('token') == slack_slash_token:
        t = PrettyTable(['User Name','User ID'])
        for user in user_list['members']:
	    t.add_row([user['id'],user['profile']['real_name']])
	data = "```" + t.get_string() + "```"
        return Response(data, status=200)
    return Response("invalid slack token", status=200)	    
        

if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
