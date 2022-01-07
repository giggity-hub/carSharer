from flask import Flask, request, render_template
import user
import connect
# from connect import DBUtil
from userStore import UserStore
# import userStore
import threading
import csv
import re
from currentUser import CurrentUser

current_user = CurrentUser()
app = Flask(__name__, template_folder='template')

userList = []
userList.append(user.User("Bill", "Gates"))
userList.append(user.User("Steve", "Jobs"))
userList.append(user.User("Larry", "Page"))
userList.append(user.User("Sergey", "Brin"))
userList.append(user.User("Larry", "Ellison"))


def csv_reader(path):
    with open(path, "r") as csvfile:
        tmp = {}
        reader = csv.reader(csvfile, delimiter='=')
        for line in reader:
            tmp[line[0]] = line[1]
    return tmp


config = csv_reader("properties.settings")

@app.route('/view_drive/<fahrt_id>', methods=['GET'])
def view_driveGet(fahrt_id):
    # gette die fahrt zur id und render die in nem passenden template
    return fahrt_id


@app.route('/view_main', methods=['GET'])
def view_mainGet():
    conn = connect.DBUtil().getExternalConnection()
    curs = conn.cursor()
    # Reservierte Fahrten
    curs.execute(f"select * from fahrt where fid in (select fahrt from reservieren where kunde='{current_user.getID()}')")
    reservierte_fahrten =  curs.fetchall()
    
    # Offene Fahrten
    curs.execute(f"select * from fahrt where status='offen'")
    offene_fahrten = curs.fetchall()
    print(f"{reservierte_fahrten=}, {offene_fahrten=}")
    return render_template('index.html', 
        reservierte_fahrten=reservierte_fahrten, 
        offene_fahrten=offene_fahrten
    )
    #1.) alle vom nutzer reservierten fahrten getten
    # 2.) alle noch freien fahrten getten


@app.route('/hello', methods=['GET'])
@app.route("/", methods=["GET"])
def helloGet():
    return render_template('hello.html', users=userList)


@app.route('/hello', methods=['POST'])
def helloPost():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    return f"{firstname}, {lastname}"

    # if firstname is not None and lastname is not None and firstname and lastname:
    #     with threading.Lock():
    #         userList.append(user.User(firstname, lastname))

    # return render_template('hello.html', users=userList)


@app.route('/carSharer', methods=['GET'])
def carShare():
    try:
        dbExists = connect.DBUtil().checkDatabaseExistsExternal()
        if dbExists:
            db2exists = 'vorhanden! Supi!'
        else:
            db2exists = 'nicht vorhanden :-('
    except Exception as e:
        print(e)

    return render_template('carSharer.html', db2exists=db2exists)


@app.route('/addUser', methods=['GET'])
def addUser():
    userSt = UserStore()
    try:
        # userSt = {}
        
        userToAdd = user.User("Max", "Mustermann")
        moped = userSt.addUser(userToAdd)
        print(moped)
        # userSt.addUser(userToAdd)
        # userSt.completion()

        return "saaaaaaaas"
        # ...
        # mach noch mehr!
    except Exception as e:
        print(e)
        return "Failed!"
    finally:
        userSt.close()



if __name__ == "__main__":
    port = int("9" + re.match(r"([a-z]+)([0-9]+)", config["username"], re.I).groups()[1])
    host = 'localhost'
    app.run(host=host, port=port, debug=True)
