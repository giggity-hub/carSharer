from stores.basestore import Store
from utils import tupleList2dictList

class VehicleStore(Store):
    def get_vehicles(self):
        curs = self.conn.cursor()
        curs.execute("""SELECT tid, name, icon FROM transportmittel""")
        transportmittel_tupel = curs.fetchall()
        columns = ['tid', 'name', 'icon']
        return tupleList2dictList(transportmittel_tupel, columns)
