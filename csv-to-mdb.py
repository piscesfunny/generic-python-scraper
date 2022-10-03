import os
import pypyodbc
import pyodbc
from utils.config import BASE_DIR, OUTPUT_RESULT_DIR


for f in os.listdir(OUTPUT_RESULT_DIR):
    filename, file_extension = os.path.splitext(f)
    db_f_path = os.path.join(BASE_DIR, "db", f"{filename}.mdb")
    if os.path.exists(db_f_path):
        print(f"Skipped file - {f}")
        continue
    pypyodbc.win_create_mdb(db_f_path)

    # DATABASE CONNECTION
    connection_str = "DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={};".format(db_f_path)
    con = pyodbc.connect(connection_str, ansi=True)
    con.setdecoding(pyodbc.SQL_CHAR, encoding='iso-8859-1')
    con.setdecoding(pyodbc.SQL_WCHAR, encoding='iso-8859-1')
    con.setencoding(encoding='iso-8859-1')

    # RUN QUERY
    strSQL = f"SELECT * INTO [patentscope] FROM [text;HDR=Yes;FMT=Delimited(,);Database={OUTPUT_RESULT_DIR}].{f};"
    cur = con.cursor()
    cur.execute(strSQL)
    con.commit()
    con.close()
    print(f"MDB file has been created from {f}")

print("<<<")
