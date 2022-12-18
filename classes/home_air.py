#from classes.PM_detector import PM_sds011
from sds011 import SDS011
import time
import mysql.connector as mariadb
import sys
import os
import atexit
import datetime
import logging

class SM011_detector(object):
    '''
        Class to manage SDS011 and write to MariaDB database


    Return codes
        - RC 0:  Success
        - RC 1:  Generic error
        - RC 10: Cannot open sensor on USB port
    '''
    def __init__(self, USB_port, DB_IP, DB_user, DB_passwd, DB_name, min_interval=5, verbose=True):
        self.USB_port = USB_port
        self.DB_IP = DB_IP
        self.DB_user = DB_user
        self.DB_passwd = DB_passwd
        self.DB_name = DB_name
        self.verbose = verbose
        self.output_dir = "./logs/"
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.log_file = self.output_dir +  'home_air_' + self.timestamp + '.log'
        self.log = self.__log_up()
        self.__cleanup()
        self.sensor = self.__open_detector()
        self.sensor.set_working_period(rate=min_interval)
        atexit.register(self.__cleanup)

    
    def __cleanup(self):
        self.log.debug(
            "Object is being destroyed"
        )
        try:
            self.sensor.__del__()
            self.log.debug(
                "Sensor is closed"
            )
        except BaseException:
            self.log.debug(
                "Sensor did not close due it was not open"
            )


    def __create_output_dir(self):
        # Lets create the output dir
        if os.path.isdir(self.output_dir) == False:
            try:
                os.makedirs(self.output_dir)
                return True
            except BaseException:
                sys.exit("Cannot create " + self.output_dir)
        
 
    def __log_up(self):
        self.__create_output_dir()
        log_format = '%(asctime)s %(levelname)-4s:\t %(message)s'
        logging.basicConfig(level=logging.DEBUG,
                    format=log_format,
                    filename=self.log_file,
                    filemode='w')
 
        console = logging.StreamHandler()
        if self.verbose:
            console.setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(log_format))
        logging.getLogger('').addHandler(console)
        log = logging.getLogger()
        return log


    def __open_detector(self):
        self.log.debug(
            "Going to open sensor on port " +
            self.USB_port
        )
        try:
            sensor = SDS011(port=self.USB_port)
            self.log.info(
                "Sensor is open on port " +
                self.USB_port
            )
            return sensor
        except BaseException:
            self.log.error(
                "Could not open sensor on port " +
                self.USB_port
            )
            sys.exit(10)
        
        

    def read_value(self, print_value=False):
        # OrderedDict([('timestamp', datetime.datetime(2020, 5, 3, 21, 22, 27, 28476)), ('pm2.5', 5.8), ('pm10', 22.3), ('device_id', 40488)])
        self.log.debug(
            "Querying to read values from device"
        )
        #self.__wakeup_sensor()
        my_measurement = self.sensor.read_measurement()
        self.log.debug(
            "Values had been read from device. PM2.5: " +
            str(my_measurement['pm2.5']) +
            " PM10: " +
            str(my_measurement['pm10'])
        )
        if print_value:
            print(
                str(my_measurement['timestamp'].strftime('%Y-%m-%d %H:%M:%S')) +
                " --> PM 2.5: " +
                str(my_measurement['pm2.5']) +
                " | PM 10: " +
                str(my_measurement['pm10'])
            )


        #self.__sleep_sensor()
        return my_measurement


    def write_DB(self, measurement):
        '''
        CREATE TABLE `DEV_ID!` (
        -> `timestamp` DATETIME,
        -> `pm2.5` FLOAT,
        -> `pm10` FLOAT )
        -> ENGINE = InnoDB;
        '''
        self.log.debug(
            "Going to open DB connection"
        )
        try:
            mariadb_connection = mariadb.connect(
                host=self.DB_IP,
                user=self.DB_user,
                password=self.DB_passwd,
                database=self.DB_name)
            cursor = mariadb_connection.cursor()
            self.log.debug(
                "DB connection opened"
            )
        except BaseException:
            self.log.error(
                "Conection to DB failed"
            )
            return False
        sql_insert = (
            "INSERT INTO `" +
            str(measurement['device_id']) +
            "` VALUES ('" + 
            str(measurement['timestamp']) + 
            "','" + 
            str(measurement['pm2.5']) + 
            "','" + 
            str(measurement['pm10'])  +
            "');")
        self.log.debug(
            "Going to insert data into DB"
        )
        try:
            cursor.execute(sql_insert)
            mariadb_connection.commit()
            if cursor.rowcount > 0:
                self.log.debug(
                    "Insert in DB was successful"
                )
            else:
                self.log.error(
                    "Insert in DB was NOT successful"
                )
        except BaseException:
            self.log.error(
                "Insert into DB raised an error"
            )
            return False
        return True


    def __sleep_sensor(self):
        self.log.debug(
            "Going to put sensor to sleep"
        )
        self.sensor.sleep()
        self.log.debug(
            "Sensor is sleeping now"
        )
    

    def __wakeup_sensor(self):
        self.log.debug(
            "Going to wake up sensor"
        )
        self.sensor.wakeup()
        time.sleep(10)        
        self.log.debug(
            "Sensor is awake"
        )
