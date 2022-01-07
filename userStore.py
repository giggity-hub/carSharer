import connect


class UserStore:

    def __init__(self):
        #dbUtil = connect.DBUtil().getExternalConnection("testdb")
        self.conn = connect.DBUtil().getExternalConnection()
        self.conn.jconn.setAutoCommit(False)
        self.complete = None

    # PREPARED STATEMENT (WITH PLACEHOLDERS)
    def addUser(self, userToAdd):
        print('saaaaaas', userToAdd.getFirstName(), userToAdd.getLastName())
        curs = self.conn.cursor()
        print('sooooooooos', curs)
        sqlExample = "INSERT INTO USER (firstname, lastname) VALUES(?, ?)"

        # curs.execute(sqlExample, (userToAdd.getFirstName(), userToAdd.getLastName()))
        curs.execute("select * from benutzer")
        return curs.fetchall()
  

    def completion(self):
        self.complete = True

    def close(self):
        if self.conn is not None:
            try:
                if self.complete:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except Exception as e:
                print(e)
            finally:
                try:
                    self.conn.close()
                except Exception as e:
                    print(e)
