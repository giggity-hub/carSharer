from datetime import date
from flask import Flask, request, render_template, redirect, url_for, flash, abort
from stores.bookingstore import BookingStore
from stores.driveStore import DriveStore
from stores.vehiclestore import VehicleStore
import stores.driveStore as driveStore
import stores.ratingstore as ratingstore
import re
from currentUser import CurrentUser
import date_time_util
from app import app
from utils import *
from jaydebeapi import DatabaseError

current_user = CurrentUser()


# refactored

# Error 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title='404'), 404


# View Main
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


# New Rating
@app.route("/new_rating/<fahrt_id>", methods=["POST"])
def new_rating_post(fahrt_id):

    with ratingstore.RatingStore() as rs, DriveStore() as ds:
        try:
            bewertung = request.form.get("bewertungstext")
            rating = request.form.get("rating")
            driveExists = ds.get_drive(fahrt_id)

            # Inut Validation
            assert driveExists, "Diese Fahrt existiert nicht"
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
        except DatabaseError:
            flash("Allgemein Fehler mit der Datenbank.", "error")
            return redirect("/view_drive/" + str(fahrt_id))


# View Drive
@app.route('/view_drive/<fahrt_id>', methods=['GET'])
def view_driveGet(fahrt_id):
    with driveStore.DriveStore() as ds:
        fahrt = ds.get_drive(fahrt_id)
        durchschnitt_rating = ds.get_avg_rating(fahrt_id)
        bewertungen = ds.get_bewertungen(fahrt_id)

        return render_template('view_drive.html', fahrt=fahrt, durchschnitt_rating=durchschnitt_rating,
                               bewertungen=bewertungen)


@app.route("/view_search", methods=["GET"])
def view_search_get():
    return render_template("view_search.html")


@app.route("/view_search", methods=["POST"])
def view_search_post():
    start = request.form.get("Start").upper()
    ziel = request.form.get("Ziel").upper()
    datum = request.form.get("Datum")

    # print((not start and ziel) or (start and not ziel))
    if not (start and ziel and datum):
        flash("Startort Zielort und Datum müssen angegeben werden", "error")
        return redirect("/view_search")

    # Startort, Zielort, Fahrtkosten und Icon holen:
    with driveStore.DriveStore() as ds:
        fahrten = ds.get_search_request(start, ziel, datum)
        return render_template("view_search.html", fahrten=fahrten)


# Reservieren
@app.route('/reservieren/<fahrt_id>', methods=['POST'])
def view_drive_reservieren(fahrt_id):
    with BookingStore() as bs, driveStore.DriveStore() as ds:

        fahrt = ds.get_drive(fahrt_id)
        uid = current_user.getID()
        anzahl_plaetze = int(request.form["anzahl_plaetze"])

        try:
            assert fahrt['status'] == 'offen', "Geschlossene Fahrten können nicht reserviert werden"
            assert anzahl_plaetze in [1, 2], "Es dürfen nur 1 oder 2 Plätze reserviert werden"
            assert anzahl_plaetze <= int(
                fahrt['freiePlaetze']), "Es dürfen nicht mehr Plätze reserviert werden als offen sind"
            assert int(fahrt["anbieter"]) != int(
                uid), "Sie sind der Anbieter dieser Fahrt und dürfen diese nicht reservieren"
            assert not bs.has_user_booked_drive(uid,
                                                fahrt_id), "Sie haben für diese Fahrt bereits eine reservierung vorgenommen"
        except AssertionError as error_message:
            flash(str(error_message), "error")
            return redirect("/view_drive/" + str(fahrt_id))
        except DatabaseError:
            flash("Allgemein Fehler mit der Datenbank.", "error")
            return redirect("/view_drive/" + str(fahrt_id))

        bs.book_drive(current_user.getID(), fahrt_id, anzahl_plaetze)
        flash("Die Fahrt wurde erfolgreich reserviert", "info")
        return redirect(f'/view_drive/{fahrt_id}')


@app.route("/new_drive", methods=["GET"])
def new_drive_get():
    with VehicleStore() as vs:
        transportmittel = vs.get_vehicles()
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
    beschreibung = f"'beschreibung'" if beschreibung else "NULL"

    with DriveStore() as ds:
        try:
            assert zielort, "Zielort darf nicht leer sein"
            assert startort, "Startort darf nicht leer sein"
            assert maxPlaetze.isnumeric(), "Anzahl an Plätzen muss eine positive Zahl sein"
            assert int(maxPlaetze) > 0 and int(maxPlaetze) <= 10, "Die Anzahl an Plätzen muss zwischen 1 und 10 liegen"
            assert kosten.isnumeric(), "Die Fahrtkosten müssen eine positive Ganzzahl sein"
            assert date_time_util.isFutureDate(datum), "Das eingegebene Datum liegt in der Vergangenheit."
            assert len(beschreibung) <= 50, "Die Länge der Beschreibung darf maximal 50 Zeichen lang sein"

            ds.create_drive(
                startort,
                zielort,
                date_time_util.html_date_time_2_DB2DateTime(datum, zeit),
                maxPlaetze,
                kosten,
                current_user.getID(),
                transportmittel,
                beschreibung
            )
            flash("Die Fahrt wurde erfolgreich hinzugefügt", "info")
            return redirect(url_for("view_mainGet"))

        except AssertionError as error_message:
            flash(str(error_message), "error")
            return redirect("/new_drive")
        except DatabaseError:
            flash("Allgemein Fehler mit der Datenbank.", "error")
            return redirect(url_for("new_drive_get"))


@app.route("/new_rating/<fahrt_id>", methods=["GET"])
def new_rating_get(fahrt_id):
    with DriveStore() as ds:
        driveExists = ds.get_drive(fahrt_id)
        if not driveExists:
                abort(404)
        return render_template("new_rating.html")


# not refactored


@app.route('/delete/<fahrt_id>', methods=['POST'])
def view_drive_delete(fahrt_id):
    # checken ob der User auch der Anbieter der Fahrt ist
    with DriveStore() as ds:
        fahrt = ds.get_drive(fahrt_id)
        uid = current_user.getID()

        if int(fahrt['anbieter']) != int(uid):
            flash("Sie sind nicht der Anbieter und daher nicht berechtigt diese Fahrt zu löschen", "error")
            return redirect("/view_drive/" + str(fahrt_id))

        ds.delete_drive(fahrt_id)
        flash("Fahrt wurde gelöscht", "info")
        return redirect(url_for('view_mainGet'))


@app.route("/bonus", methods=["GET"])
def bonus():
    with driveStore.DriveStore() as ds:
        bester_fahrer = ds.get_id_max_avg_rating()
        beste_offene_fahrten = ds.get_open_drives_users(bester_fahrer[0])
        print(beste_offene_fahrten)
        print(bester_fahrer)
    return render_template("bonus.html", beste_offene_fahrten=beste_offene_fahrten, bester_fahrer=bester_fahrer)


config = csv_reader("properties.settings")

if __name__ == "__main__":
    port = int("9" + re.match(r"([a-z]+)([0-9]+)", config["username"], re.I).groups()[1])
    host = 'localhost'
    app.run(host=host, port=port, debug=True)
