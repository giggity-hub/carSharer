from stores.basestore import Store

class BookingStore(Store):
    def book_drive(self, uid, fid, seats):
        curs = self.conn.cursor()
        pstmt = "insert into Reservieren (kunde, fahrt, anzPlaetze) VALUES (?, ?, ?)"
        curs.execute(pstmt, (uid, fid, seats))

    def has_user_booked_drive(self, uid, fid):
        curs = self.conn.cursor()
        pstmt = "select * from Reservieren where kunde=? and fahrt=?"
        curs.execute(pstmt, (uid, fid))
        return bool(curs.fetchone())

