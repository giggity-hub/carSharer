import connect


class Store(object):

    def __init__(self):
        self.con = None
        self.complete = None

        self.conn = connect.DBUtil().getExternalConnection()
        self.conn.jconn.setAutoCommit(False)
        self.complete = None

    def __enter__(self):
        self.conn = connect.DBUtil().getExternalConnection()
        self.conn.jconn.setAutoCommit(False)
        self.complete = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.completion()
        self.close()

    # PREPARED STATEMENT (WITH PLACEHOLDERS)
    # def addUser(self, userToAdd):
    #     curs = self.conn.cursor()
    #     sqlExample = "INSERT INTO USER (firstname, lastname) VALUES(?, ?)"
    #     curs.execute(sqlExample, (userToAdd.getFirstName(), userToAdd.getLastName()))

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
