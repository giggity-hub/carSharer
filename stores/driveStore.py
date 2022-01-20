import connect
from stores.basestore import Store
from utils import clob2string, tuple2dict
from flask import abort
from jpype import JavaException
import date_time_util


class DriveStore(Store):

    def getDrivesForUser(self, uid):
        curs = self.conn.cursor()
        curs.execute("""select f.fid, t.icon, f.startort, f.zielort, f.status
                        from fahrt f, transportmittel t
                        where f.fid in (select fahrt from reservieren where kunde=?) and t.tid = f.transportmittel""",
                     (uid))
        return curs.fetchall()

    def getOpenDrives(self):
        curs = self.conn.cursor()
        curs.execute("""select f.fid, t.icon, f.startort, f.zielort, (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze, f.fahrtkosten
                            from fahrt f, transportmittel t, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                                                        from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                                                        GROUP BY FID) tmp
                            where tmp.fid = f.fid and t.tid = f.transportmittel and f.STATUS = 'offen'""")
        return curs.fetchall()

    def get_open_drives_users(self, user_id):
        curs = self.conn.cursor()
        curs.execute("""select f.fid, t.icon, f.startort, f.zielort, (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze, f.fahrtkosten, f.status, f.anbieter
                            from fahrt f, transportmittel t, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                                                                from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                                                                GROUP BY FID) tmp
                            where f.anbieter=? and tmp.fid =f.fid and t.tid = f.transportmittel and f.STATUS = 'offen'""", (user_id,))
        return curs.fetchall()

    def get_bewertungen(self, fahrt_id):
        curs = self.conn.cursor()
        #  alle Bewertungen zu der Fahrt getten
        curs.execute("""   select ben.EMAIL, bew.TEXTNACHRICHT, bew.RATING from SCHREIBEN s,
                                              (select EMAIL, BID from BENUTZER) ben,
                                              (select BEID, TEXTNACHRICHT, RATING, ERSTELLUNGSDATUM from BEWERTUNG) bew
                                where s.FAHRT =? and s.BENUTZER = ben.BID and s.BEWERTUNG = bew.BEID
                                order by bew.ERSTELLUNGSDATUM desc """, (fahrt_id,))

        # Alle CLOBs in Strings umwandeln.
        bewertungen = []
        bewertung = curs.fetchone()
        while bewertung:
            bewertung = list(bewertung)
            bewertung[1] = clob2string(bewertung[1])
            bewertungen.append(bewertung)
            bewertung = curs.fetchone()
        return bewertungen

    def get_avg_rating(self, fid):
        # Average Rating
        curs = self.conn.cursor()
        curs.execute("""   select AVG( cast(b.RATING as decimal(4,2))) as Durchschnitt from SCHREIBEN s,
                                    (select * from BEWERTUNG) b
                        where s.FAHRT =? and s.BEWERTUNG = b.BEID""", (fid,))
        durchschnitt_rating = curs.fetchone()
        try:
            durchschnitt_rating = round(durchschnitt_rating[0], 2)
        except TypeError:
            durchschnitt_rating = 0

        return durchschnitt_rating

    def get_id_max_avg_rating(self):
        # Maximum Average Rating
        curs = self.conn.cursor()
        curs.execute(""" select * from
                            (select *
                            from
                            (select tmp2.anbieter, AVG(tmp2.durchschnitt) as nutzer_schnitt
                            from(select tmp.fahrt, tmp.anbieter, AVG( cast(tmp.RATING as decimal(4,2))) as Durchschnitt
                            from (select *
                            from
                            (select s.benutzer, s.fahrt, b.beid, b.rating
                            from Schreiben s join Bewertung b
                            on s.bewertung = b.beid
                            order by s.fahrt) t join
                            (select fid, anbieter
                            from fahrt
                            order by fid) f
                            on f.fid=t.fahrt
                            order by anbieter) tmp
                            group by tmp.fahrt, tmp.anbieter) tmp2
                            group by tmp2.anbieter) tmp5
                            inner join
                            (select max(tmp3.nutzer_schnitt) as Megamaximum
                            from (select tmp2.anbieter, AVG(tmp2.durchschnitt) as nutzer_schnitt
                            from(select tmp.fahrt, tmp.anbieter, AVG( cast(tmp.RATING as decimal(4,2))) as Durchschnitt
                            from (select *
                            from
                            (select s.benutzer, s.fahrt, b.beid, b.rating
                            from Schreiben s join Bewertung b
                            on s.bewertung = b.beid
                            order by s.fahrt) t join
                            (select fid, anbieter
                            from fahrt
                            order by fid) f
                            on f.fid=t.fahrt
                            order by anbieter) tmp
                            group by tmp.fahrt, tmp.anbieter) tmp2
                            group by tmp2.anbieter) tmp3) tmp4
                            on tmp4.Megamaximum = tmp5.nutzer_schnitt) final
                            join Benutzer b2
                            on final.ANBIETER=b2.BID
""")
        Bester_Fahrer = curs.fetchone()
        return Bester_Fahrer

    def get_drive(self, fid):
        try:
            curs = self.conn.cursor()

            curs.execute("""select f.fid, f.anbieter, f.startort, f.zielort, f.fahrtdatumzeit, f.maxPlaetze, f.fahrtkosten, f.status, f.beschreibung,
                                    b.email, t.icon
                            from fahrt f, benutzer b, transportmittel t
                            where f.fid=? and b.bid=f.anbieter and t.tid=f.transportmittel """, (fid,))
            fahrtTupel = curs.fetchone()

            if not fahrtTupel:
                abort(404)

            print(fahrtTupel)
            fahrtTupel += (clob2string(fahrtTupel[8]),)
            columns = ['fid', 'anbieter', 'startort', 'zielort', 'fahrtdatumzeit', 'maxPlaetze', 'fahrtkosten',
                       'status', 'beschreibung', 'email', 'icon', 'beschreibung_string']
            fahrt = tuple2dict(fahrtTupel, columns)
            # fahrt["beschreibung_string"] = clob2string(fahrt["beschreibung"])

            # Freie Plaetze
            curs.execute("""select (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze
                        from fahrt f, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                            from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                            GROUP BY FID) tmp
                        where tmp.fid = f.fid and f.fid=?""", (fid,))
            fahrt["freiePlaetze"] = curs.fetchone()[0]

            return fahrt

        except JavaException as e:
            abort(404)

    def get_search_request(self, start, ziel, datum):
        # Startort, Zielort, Fahrtkosten und Icon holen:
        curs = self.conn.cursor()
        curs.execute(f"""   SELECT f.FID, f.STARTORT, f.ZIELORT,f.FAHRTKOSTEN, t.ICON
                            from TRANSPORTMITTEL t, (Select STARTORT, ZIELORT, FAHRTKOSTEN, TRANSPORTMITTEL, FID
                                                    from FAHRT
                                                    WHERE STATUS = 'offen'
                                                        and upper(STARTORT) like ?
                                                        and upper(ZIELORT) like ?
                                                        and FAHRTDATUMZEIT >= ?) f 
                            where f.TRANSPORTMITTEL = t.TID""",
                     (f"%{start}%", f"%{ziel}%", date_time_util.html_date_2_DB2DateTime(datum)))
        return curs.fetchall()

    def delete_drive(self, fid):
        # fahrt, schreiben, bewertungen und reservierungen löschen müssen zusammen passieren damit rollback funzen kann
        curs = self.conn.cursor()

        # alle Bewertungs-ids für die zu löschende Fahrt holen
        curs.execute(f"""   select b.BEID
                            from BEWERTUNG b,
                                 (select * from SCHREIBEN where FAHRT = {fid}) s
                            where s.BEWERTUNG = b.BEID""")

        bewertung_ids = []
        for bewertung in curs.fetchall():
            bewertung_ids.append(bewertung[0])

        if bewertung_ids:
            bewertung_ids = str(bewertung_ids).replace("[", "(").replace("]", ")")

            curs.execute(f"delete from SCHREIBEN where FAHRT = ?", (fid, ))
            curs.execute(f"delete from BEWERTUNG where BEID in {bewertung_ids}")

        curs.execute(f"delete from RESERVIEREN where FAHRT = ?", (fid, ))
        curs.execute(f"delete from FAHRT where FID = ?", (fid, ))

        # curs.execute("delete from Reservieren where fahrt=?", (fid,))
        # curs.execute("delete from Bewertung where beid in (select bewertung from FINAL TABLE (delete from schreiben where fahrt=?))", (fid,))
        # curs.execute("delete from fahrt where fid=?", (fid,))

    def create_drive(self, startort, zielort, datumzeit, maxPlaetze, kosten, uid, tid, beschreibung):
        curs = self.conn.cursor()
        pstmt = """INSERT INTO fahrt (startort, zielort, fahrtdatumzeit, maxPlaetze,
                    fahrtkosten, anbieter, transportmittel, beschreibung)  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        curs.execute(pstmt, (startort, zielort, datumzeit, maxPlaetze, kosten, uid, tid, beschreibung))
