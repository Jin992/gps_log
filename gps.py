import pynmea2, serial, os, time, sys, glob
import datetime
import pytz
from datetime import timezone

epoch = datetime.datetime.utcfromtimestamp(0)
gps_qual = 0
num_sats = 0
alt = 0.0   

def unix_time(dt):
    return (dt - epoch).total_seconds()

def _scan_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        patterns = ('/dev/ttyUSB*', '/dev/ttyUSB*')
        ports = [glob.glob(pattern) for pattern in patterns]
        ports = [item for sublist in ports for item in sublist]  # flatten
    elif sys.platform.startswith('darwin'):
        patterns = ('/dev/ttyUSB*')
        ports = [glob.glob(pattern) for pattern in patterns]
        ports = [item for sublist in ports for item in sublist]  # flatten
    else:
        raise EnvironmentError('Unsupported platform')
    return ports

def logfilename():
    now = datetime.datetime.now()
    return '/home/pi/Desktop/NMEA_%0.4d-%0.2d-%0.2d.txt' % \
                (now.year, now.month, now.day)            

try:
    while True:
        ports = _scan_ports()
        if len(ports) == 0:
            sys.stderr.write('No ports found, waiting 10 seconds...press Ctrl-C to quit...\n')
            time.sleep(10)
            continue

        for port in ports:
            # try to open serial port
            sys.stderr.write('Trying port %s\n' % port)
            try:
                # try to read a line of data from the serial port and parse
                with serial.Serial(port, 38400) as ser:
                    # 'warm up' with reading some input
                    for i in range(10):
                        ser.readline()
                    # try to parse (will throw an exception if input is not valid NMEA)
                    pynmea2.parse(ser.readline().decode('ascii', errors='replace'))
                
                    # log data
                    outfname = logfilename()
                    sys.stderr.write('Logging data on %s to %s\n' % (port, outfname))
                    log_string = ''
                    string_cnt = 0
                    
                    # loop will exit with Ctrl-C, which raises a
                    # KeyboardInterrupt
                    while True:
                        line = ser.readline().decode('ascii', errors='replace')
                        #print(line)
                        if str(line).find('GGA') > 0:
                            msg = pynmea2.parse(line)
                            gps_qual = msg.gps_qual
                            num_sats = msg.num_sats
                            alt = "{0:.1f}".format(msg.altitude)
                        if str(line).find('RMC') > 0:
                            msg = pynmea2.parse(line)
                            local_time = msg.datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)
                            if string_cnt < 50:
                                log_string += str(local_time.strftime('%Y-%m-%d %H:%M:%S.%f')[0:21] + "," + str(int(unix_time(msg.datetime))) + "," + str("{0:.6f}".format(msg.latitude)) + "," + str("{0:.6f}".format(msg.longitude)) + "," + str(alt) + "," + str(gps_qual) + "," + str(num_sats) + "\r\n")
                                string_cnt += 1
                            else:
                                log_string += str(local_time.strftime('%Y-%m-%d %H:%M:%S.%f')[0:21] + "," + str(int(unix_time(msg.datetime))) + "," + str("{0:.6f}".format(msg.latitude)) + "," + str("{0:.6f}".format(msg.longitude)) + "," + str(alt) + "," + str(gps_qual) + "," + str(num_sats) + "\r\n")
                                with open(outfname, 'a') as f:
                                    f.write(log_string)
                                    f.close()
                                log_string = ''
                                string_cnt = 0

            except Exception as e:
                sys.stderr.write('Error reading serial port %s: %s\n' % (type(e).__name__, e))
            except KeyboardInterrupt as e:
                sys.stderr.write('Ctrl-C pressed, exiting log of %s to %s\n' % (port, outfname))

        sys.stderr.write('Scanned all ports, waiting 10 seconds...press Ctrl-C to quit...\n')
        time.sleep(1)
except KeyboardInterrupt:
    sys.stderr.write('Ctrl-C pressed, exiting port scanner\n')
