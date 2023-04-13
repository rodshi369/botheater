# -*- coding: utf-8 -*-

# import modbus_tk
import modbus_tk.defines as cst
# import modbus_tk.modbus_tcp as modbus_tcp
# import sqlite3
import datetime
import time
import db, connect_TCP


def logging(q):
    while True:
        paket1 = connect_TCP.read_unit(1, cst.READ_HOLDING_REGISTERS, 3137, 3)
        if paket1 == None:
            temp = (0, 0, 0)
        else:
            temp = paket1

        paket2 = connect_TCP.read_unit(1, cst.READ_COILS, 1538, 1)
        if paket2 == None:
            condition = (0)
        else:
            condition = paket2

        paket3 = connect_TCP.read_unit(1, cst.READ_HOLDING_REGISTERS, 3072, 15)
        if paket3 == None:
            setpoints = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            setpoints = paket3
        dt = datetime.datetime.now()
        sostoyanie = None if paket1==None and paket2==None and paket3==None else True
        # Отправим данные в основной поток
        q.put_nowait((temp, condition, setpoints, dt, sostoyanie))
        ################################

        try:
            if temp[1] <= setpoints[1]:
                param = (dt, float(temp[0] / 10), float(temp[1] / 10), float(temp[2] / 10), condition[0], "Низкая темп.притока")
            elif temp[2] <= setpoints[2]:
                param = [dt, float(temp[0] / 10), float(temp[1] / 10), float(temp[2] / 10), condition[0], "Низкая темп.обратки"]
            else:
                param = [dt, float(temp[0] / 10), float(temp[1] / 10), float(temp[2] / 10), condition[0], " "]

            db.add_record_log(param)
        except Exception as err:
            print(err)

        #   Проверим заполненость базы

        rez = db.get_record_log("SELECT COUNT(id) FROM log ", None)
        if rez is not None:
            one_result = rez.fetchall()
            if one_result[0][0] >= 86400:  # 86400 примерно 10 дней
                db.shrink_log()
        rez = db.get_record_log("SELECT COUNT(id) FROM passing ", None)
        if rez is not None:
            one_result = rez.fetchall()
            if one_result[0][0] >= 3000:  # 60480 примерно 10 дней
                db.shrink_passing()

        ###############################################
        time.sleep(10)


if __name__ == "__main__":
    logging()
