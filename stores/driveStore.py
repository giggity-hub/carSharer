import connect
from stores.basestore import Store
from utils import clob2string
import date_time_util


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
