import connect
from stores.basestore import Store

class DriveStore(Store):

    def getDrivesForUser(self, uid):
        curs = self.conn.cursor()
        curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, f.status
                        from fahrt f, transportmittel t
                        where f.fid in (select fahrt from reservieren where kunde=?) and t.tid = f.transportmittel""", (uid))
        return curs.fetchall()

    def getOpenDrives(self):
        curs = self.conn.cursor()
        curs.execute(f"""select f.fid, t.icon, f.startort, f.zielort, (f.maxPlaetze - tmp.belegtePlaetze) as freiePlaetze, f.fahrtkosten
                    from fahrt f, transportmittel t, (select coalesce(sum(ANZPLAETZE),0) as belegtePlaetze, FID
                                                        from FAHRT left join RESERVIEREN R on FAHRT.FID = R.FAHRT
                                                        GROUP BY FID) tmp
                    where tmp.fid = f.fid and t.tid = f.transportmittel and f.STATUS = 'offen'""")
        return curs.fetchall()
