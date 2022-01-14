import connect
from stores.basestore import Store

class RatingStore(Store):

    def userHasNotRated(self, bid, fid):
        curs = self.conn.cursor()
        curs.execute(f"""   select BENUTZER,FAHRT 
                            from SCHREIBEN
                            where BENUTZER =? and FAHRT=?""", (bid, fid))
        return not bool(curs.fetchone())

    def addRating(self, bid, fid, text, rating):
        curs = self.conn.cursor()
        print(bid, fid, text, rating)
        curs.execute(f""" Select BEID from new table(INSERT INTO bewertung (textnachricht, erstellungsdatum, rating) VALUES
                                ( ? ,CURRENT TIMESTAMP, ?))""", (text, rating))
        rid = curs.fetchall()[0][0]
        print(rid)

        # Bewertung zu SCHREIBEN hinzufügen
        curs.execute(f"""   Insert INTO SCHREIBEN (BENUTZER, FAHRT, BEWERTUNG) VALUES 
                            (?,?,?)""", (bid, fid, rid))