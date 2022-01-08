from flask import Flask, request, render_template, redirect, url_for, flash
import user
import connect
# from connect import DBUtil
from userStore import UserStore
# import userStore
import threading
import csv
import re
from currentUser import CurrentUser
import date_time_util

current_user = CurrentUser()
app = Flask(__name__, template_folder='template', static_url_path='/pfad')
app.secret_key = "superSecretKey"

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
    curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, f.status 
                        from fahrt f, transportmittel t
                        where f.fid in (select fahrt from reservieren where kunde='{current_user.getID()}') and t.tid = f.transportmittel""")
    reservierte_fahrten = curs.fetchall()

    # Offene Fahrten
    curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze, f.fahrtkosten
                    from fahrt f, transportmittel t, (select f.fid, SUM(r.anzPlaetze) as belegtePlaetze 
                        from fahrt f, reservieren r
                        WHERE r.fahrt = f.fid
                        GROUP BY fid) tmp
                    where tmp.fid = f.fid and t.tid = f.transportmittel""")
    offene_fahrten = curs.fetchall()
    print(f"{reservierte_fahrten=}, {offene_fahrten=}")
    return render_template('index.html',
                           reservierte_fahrten=reservierte_fahrten,
                           offene_fahrten=offene_fahrten
                           )
    # 1.) alle vom nutzer reservierten fahrten getten
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


@app.route("/new_drive", methods=["GET"])
def new_drive_get():
    conn = connect.DBUtil().getExternalConnection()
    curs = conn.cursor()
    curs.execute("""SELECT tid, name FROM transportmittel""")
    transportmittel = curs.fetchall()
    return render_template("new_drive.html", transportmittel=transportmittel)


@app.route("/new_drive", methods=["POST"])
def new_drive_post():
    startort = request.form["Startort"]
    zielort = request.form["Zielort"]
    maxPlaetze = request.form["maxPlaetze"]
    kosten = request.form["Kosten"]
    transportmittel = request.form["Transportmittel"]
    datum = request.form["Fahrtdatum"]
    zeit = request.form["time"]
    beschreibung = request.form["Beschreibung"]
    if not beschreibung:
        beschreibung = "NULL"
    else:
        beschreibung = "'" + beschreibung + "'"

    # Error handling
    if not maxPlaetze.isnumeric():
        flash("Anzahl an Plätzen muss eine positive Zahl sein", "error")
        return redirect(url_for("new_drive_get"))

    if int(maxPlaetze) >= 0 and int(maxPlaetze) > 10:
        flash("Die Anzahl an Plätzen darf maximal 10 betragen", "error")
        return redirect(url_for("new_drive_get"))

    if not kosten.isnumeric():
        flash("Die Fahrtkosten müssen eine positive Ganzzahl sein", "error")
        return redirect(url_for("new_drive_get"))

    if not date_time_util.check_date_validity(datum):
        flash("Das eingegebene Datum liegt in der Vergangenheit.", "error")
        return redirect(url_for("new_drive_get"))

    if len(beschreibung) > 50:
        flash("Die Länge der Beschreibung darf maximal 50 Zeichen lang sein", "error")
        return redirect(url_for("new_drive_get"))

    try:
        # Fahrt zu DB hinzufügen
        conn = connect.DBUtil().getExternalConnection()
        curs = conn.cursor()
        curs.execute(f"""INSERT INTO fahrt (startort, zielort, fahrtdatumzeit, maxPlaetze,
                                            fahrtkosten, anbieter, transportmittel, beschreibung)  VALUES 
                                ('{startort}', '{zielort}', '{date_time_util.html_date_time_2_DB2DateTime(datum, zeit)}', {maxPlaetze},
                                 {kosten}, {current_user.getID()}, {transportmittel}, {beschreibung} )""")

    except Exception as e:
        print(e)
        flash("Allgemein Fehler mit der Datenbank.", "error")
        return redirect(url_for("new_drive_get"))

    flash("Die Fahrt wurde erfolgreich hinzugefügt", "info")
    return redirect(url_for("view_mainGet"))


@app.route("/new_rating/<fahrt_id>", methods=["GET"])
def new_rating_get(fahrt_id):
    return render_template("new_rating.html")


@app.route("/new_rating/<fahrt_id>", methods=["POST"])
def new_rating_post(fahrt_id):
    bewertung = request.form.get("Bewertung")
    rating = request.form.get("rating")

    # Error Handling
    if not bewertung:
        flash("Die Bewertung darf nicht leer sein!", "error")
        return redirect("/view_drive/" + str(fahrt_id))

    try:
        conn = connect.DBUtil().getExternalConnection()
        curs = conn.cursor()
        # check ob der User die Fahrt schon bewertet hat:
        curs.execute(f"""   select BENUTZER,FAHRT 
                            from SCHREIBEN
                            where BENUTZER = {current_user.getID()} and FAHRT= {fahrt_id}""")
        bewertung_already_exists = curs.fetchall()

        if not bewertung_already_exists:
            # !!! Bewertung wird erstellt aber SCHREIBEN wird noch nicht aktualisiert !!!!
            print(curs.execute(f""" INSERT INTO bewertung (textnachricht, erstellungsdatum, rating) VALUES
                                    ('{bewertung}',CURRENT TIMESTAMP,{rating})"""))

        else:
            flash("Sie haben für diese Fahrt bereits eine Bewertung abgegeben", "error")
            return redirect("/view_drive/" + str(fahrt_id))

    except Exception as e:
        print(e)
        return redirect("/view_drive/" + str(fahrt_id))

    flash("Die Bewertung wurde erfolgreich hinzugefügt")
    return redirect("/view_drive/" + str(fahrt_id))


if __name__ == "__main__":
    port = int("9" + re.match(r"([a-z]+)([0-9]+)", config["username"], re.I).groups()[1])
    host = 'localhost'
    app.run(host=host, port=port, debug=True)
