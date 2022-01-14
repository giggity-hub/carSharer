from aifc import Error
from datetime import date
from typing import final
from flask import Flask, request, render_template, redirect, url_for, flash
from stores.driveStore import DriveStore
import user
import connect
# from connect import DBUtil
from userStore import UserStore
import stores.driveStore as driveStore
import stores.ratingstore as ratingstore
# import userStore
import re
from currentUser import CurrentUser
import date_time_util
from app import app
from utils import *

current_user = CurrentUser()


# refactored
@app.route("/", methods=["GET"])
@app.route('/view_main', methods=['GET'])
def view_mainGet():
    ds = driveStore.DriveStore()
    try:
        reservierte_fahrten = ds.getDrivesForUser(current_user.getID())
        offene_fahrten = ds.getOpenDrives()
        ds.completion()
        return render_template('view_main.html',
                               reservierte_fahrten=reservierte_fahrten,
                               offene_fahrten=offene_fahrten
                               )
    except Exception as e:
        print(e)
    finally:
        ds.close()


@app.route("/new_rating/<fahrt_id>", methods=["POST"])
def new_rating_post(fahrt_id):
    rs = ratingstore.RatingStore()
    try:
        bewertung = request.form.get("bewertungstext")
        rating = request.form.get("rating")

        # Inut Validation
        assert bewertung, "Die Bewertung darf nicht leer sein!"
        assert rating, "Rating darf nicht leer sein"
        assert rs.userHasNotRated(current_user.getID(),
                                  fahrt_id), "Sie haben für diese Fahrt bereits eine Bewertung abgegeben"

        rs.addRating(current_user.getID(), fahrt_id, bewertung, rating)
        rs.completion()
        flash("Die Bewertung wurde erfolgreich hinzugefügt", "info")
        return redirect("/view_drive/" + str(fahrt_id))

    except AssertionError as error_message:
        flash(str(error_message), "error")
        return redirect("/view_drive/" + str(fahrt_id))

    except Error as e:
        pass

    finally:
        rs.close()


@app.route("/view_search", methods=["GET"])
def view_search_get():
    return render_template("view_search.html")


@app.route("/view_search", methods=["POST"])
def view_search_post():
    start = request.form.get("Start").upper()
    ziel = request.form.get("Ziel").upper()
    datum = request.form.get("Datum")

    print((not start and ziel) or (start and not ziel))

    # Startort, Zielort, Fahrtkosten und Icon holen:
    with driveStore.DriveStore() as ds:
        fahrten = ds.get_search_request(start, ziel, datum)

    return render_template("view_search.html", fahrten=fahrten)


# not refactored


@app.route('/view_drive/<fahrt_id>', methods=['GET'])
def view_driveGet(fahrt_id):
    # gette die fahrt zur id und render die in nem passenden template
    conn = connect.DBUtil().getExternalConnection()
    curs = conn.cursor()

    columns = 'fid, startort, zielort, fahrtdatumzeit, maxPlaetze, fahrtkosten, status, beschreibung, email, icon'
    curs.execute(f"""select f.fid, f.startort, f.zielort, f.fahrtdatumzeit, f.maxPlaetze, f.fahrtkosten, f.status, f.beschreibung,
                            b.email, t.icon
                    from fahrt f, benutzer b, transportmittel t
                    where f.fid='{fahrt_id}' and b.bid=f.anbieter and t.tid=f.transportmittel """)
    fahrtTupel = curs.fetchone()

    fahrt = dict(zip(columns.split(', '), fahrtTupel))
    fahrt["beschreibung_string"] = clob2string(fahrt["beschreibung"])

    # freie plätze berechnen
    curs.execute("""select (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze
                    from fahrt f, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                        from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                        GROUP BY FID) tmp
                    where tmp.fid = f.fid and f.fid=?""", (fahrt["fid"],))
    fahrt["freiePlaetze"] = curs.fetchone()[0]

    #  average rating getten
    curs.execute(f"""   select AVG( cast(b.RATING as decimal(4,2))) as Durchschnitt from SCHREIBEN s,
                                    (select * from BEWERTUNG) b
                        where s.FAHRT = {fahrt_id} and s.BEWERTUNG = b.BEID""")
    durchschnitt_rating = curs.fetchone()

    try:
        durchschnitt_rating = round(durchschnitt_rating[0], 2)
    except TypeError:
        durchschnitt_rating = 0

    with driveStore.DriveStore() as ds:
        bewertungen = ds.get_bewertungen(fahrt_id)

    return render_template('view_drive.html', fahrt=fahrt, durchschnitt_rating=durchschnitt_rating,
                           bewertungen=bewertungen, fahrt_id=fahrt_id)


@app.route('/reservieren/<fahrt_id>', methods=['POST'])
def view_drive_reservieren(fahrt_id):
    Anzahl_Plaetze = request.form.get("Anzahl_Plaetze")
    print(Anzahl_Plaetze)
    # Reserviere die aktuelle Fahrt, inkrementiere die Reservierung, Schalte nach Bedarf den Status um
    try:
        conn = connect.DBUtil().getExternalConnection()
        curs = conn.cursor()
        curs.execute(f"select * from fahrt where fid='{fahrt_id}'")
        fahrt = curs.fetchone()

        PreparedStatement = f"""insert into Reservieren 
                            values ('{current_user.getID()}','{fahrt_id}','{Anzahl_Plaetze}')"""
        curs.execute(PreparedStatement)

    except Exception as e:
        print(e)
    print(f"{fahrt}")
    return render_template('view_drive.html', fahrt=fahrt_id)


@app.route('/delete/<fahrt_id>', methods=['POST'])
def view_drive_delete(fahrt_id):
    # Lösche die aktuelle Reservierung, dekrementiere Reservierung um die Anzahl belegter Plätze, schalte den Status
    try:
        conn = connect.DBUtil().getExternalConnection()
        curs = conn.cursor()
        curs.execute(f"select * from fahrt where fid='{fahrt_id}'")
        fahrt = curs.fetchone()

        PreparedStatement = f"""delete from Reservieren
                                where Fahrt=({fahrt_id})"""
        curs.execute(PreparedStatement)
    except Exception as e:
        print(e)
    print(f"{fahrt}")
    return redirect(url_for(view_driveGet) + f"/{fahrt_id}")


# @app.route('/hello', methods=['GET'])
# def helloGet():
#     return render_template('hello.html', users=userList)


# @app.route('/hello', methods=['POST'])
# def helloPost():
#     firstname = request.form.get('firstname')
#     lastname = request.form.get('lastname')
#     return f"{firstname}, {lastname}"

#     # if firstname is not None and lastname is not None and firstname and lastname:
#     #     with threading.Lock():
#     #         userList.append(user.User(firstname, lastname))

#     # return render_template('hello.html', users=userList)


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
    today = date.today()
    return render_template("new_drive.html", transportmittel=transportmittel, today=today)


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

    if not zielort or not startort:
        flash("Startort und Zielort dürfen nicht leer sein", "error")
        return redirect(url_for("new_drive_get"))
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




config = csv_reader("properties.settings")

if __name__ == "__main__":
    port = int("9" + re.match(r"([a-z]+)([0-9]+)", config["username"], re.I).groups()[1])
    host = 'localhost'
    app.run(host=host, port=port, debug=True)
