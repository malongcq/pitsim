import psycopg2
from DBUtils.PooledDB import PooledDB

DSN = '''dbname=osmsgp user=postgres password=fmadmin host=10.25.180.86'''
SQL_getvehids = '''select distinct vehicle_num from %s'''
SQL_getgpslog = '''select vehicle_num, report_timestamp, x_lon, y_lat, status from %s 
    where vehicle_num='%s' order by vehicle_num, report_timestamp'''

Pool = PooledDB(psycopg2, dsn=DSN)

def get_all_vehicle_id(table):
    vehicles = []
    try:
        conn = Pool.dedicated_connection()
        curs = conn.cursor()
        curs.execute(SQL_getvehids%(table))
        for row in curs:
            #print row[0]
            vehicles.append(row[0])
        print len(vehicles),'vehicle_id loaded.'
    finally:
        conn.close()
    return vehicles
    
def get_trips_gps_log(table, veh_id):
    trips_log = []
    try:
        #conn = psycopg2.connect(DSN)
        conn = Pool.dedicated_connection()
        curs = conn.cursor()
        curs.execute(SQL_getgpslog % (table, veh_id))
        
        trip = []
        row_0 = curs.fetchone()
        for row_1 in curs:
            time_0 = row_0[1]
            lon_0 = row_0[2]
            lat_0 = row_0[3]
            pob_0 = row_0[4]

            time_1 = row_1[1]
            pob_1 = row_1[4]
            
            trip_item = (time_0, lon_0, lat_0)
            
            if pob_0 == ' POB' and pob_1 == ' POB':
                trip.append(trip_item)
            else:
                if(pob_0 == ' POB'): 
                    trip.append(trip_item)
                    trips_log.append(trip)
                trip = []
            #print row_0
            row_0 = row_1
            
        print '%s has %s trips' % (veh_id.strip(), len(trips_log))
    finally:
        conn.close()
    return trips_log