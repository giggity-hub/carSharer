import connect
from stores.basestore import Store
from utils import clob2string, tuple2dict
from flask import abort
from jpype import JavaException

class DriveStore(Store):

    def getDrivesForUser(self, uid):
        curs = self.conn.cursor()
        curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, f.status
                        from fahrt f, transportmittel t
                        where f.fid in (select fahrt from reservieren where kunde=?) and t.tid = f.transportmittel""",
                     (uid))
        return curs.fetchall()

    def getOpenDrives(self):
        curs = self.conn.cursor()
        curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze, f.fahrtkosten
                    from fahrt f, transportmittel t, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                                                        from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                                                        GROUP BY FID) tmp
                    where tmp.fid = f.fid and t.tid = f.transportmittel and f.STATUS = 'offen'""")
        return curs.fetchall()

    def get_bewertungen(self, fahrt_id):
        curs = self.conn.cursor()
        #  alle Bewertungen zu der Fahrt getten
        curs.execute(f"""   select ben.EMAIL, bew.TEXTNACHRICHT, bew.RATING from SCHREIBEN s,
                                              (select EMAIL, BID from BENUTZER) ben,
                                              (select BEID, TEXTNACHRICHT, RATING from BEWERTUNG) bew
                                where s.FAHRT = {fahrt_id} and s.BENUTZER = ben.BID and s.BEWERTUNG = bew.BEID""")

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
        curs.execute(f"""   select AVG( cast(b.RATING as decimal(4,2))) as Durchschnitt from SCHREIBEN s,
                                    (select * from BEWERTUNG) b
                        where s.FAHRT =? and s.BEWERTUNG = b.BEID""", (fid,))
        durchschnitt_rating = curs.fetchone()
        try:
            durchschnitt_rating = round(durchschnitt_rating[0], 2)
        except TypeError:
            durchschnitt_rating = 0
        
        return durchschnitt_rating

    def get_drive(self, fid):
        try:
            curs = self.conn.cursor()

            curs.execute(f"""select f.fid, f.startort, f.zielort, f.fahrtdatumzeit, f.maxPlaetze, f.fahrtkosten, f.status, f.beschreibung,
                                    b.email, t.icon
                            from fahrt f, benutzer b, transportmittel t
                            where f.fid=? and b.bid=f.anbieter and t.tid=f.transportmittel """, (fid,))
            fahrtTupel = curs.fetchone()

            if not fahrtTupel:
                abort(404)

            print(fahrtTupel)
            fahrtTupel += (clob2string(fahrtTupel[7]),)
            columns = ['fid', 'startort', 'zielort', 'fahrtdatumzeit', 'maxPlaetze', 'fahrtkosten', 'status', 'beschreibung', 'email', 'icon', 'beschreibung_string']
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

        