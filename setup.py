import os
import json
import argparse
import subprocess
import datetime
import urllib2
from pwd import getpwnam

def parse_options():
    parser = argparse.ArgumentParser(description='Setup the co2 device')
    parser.add_argument(
        '-u', '--user',
        dest='username',
        default='co2',
        help='Username to be created')
    parser.add_argument(
        '--host',
        dest='hostname',
        default='co2.example.com',
        help='Remote system hostname')
    return parser.parse_args()

def install_packages(apt, pip):
    subprocess.call(['apt-get', 'install', '-y'].extend(apt))
    subprocess.call(['pip', 'install'].extend(pip))

def setup_user(u):
    subprocess.call(['useradd', '-m', '-G', 'dialout', '-s', '/bin/bash', u])

def register(a):
    if os.path.exists('/home/' + a.username + '/etc/devicekey') and os.path.exists('/home/' + a.username + '/etc/deviceid'):
        print "Device already registered"
        return False

    req = urllib2.Request('http://' + a.hostname + '/register')
    req.add_header('Accept', 'application/json')
    req.add_header('Content-Type', 'application/json')

    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date) else None
    data = json.dumps({
        'timestamp': datetime.datetime.now()
    }, default=dthandler)
    
    try:
        res = urllib2.urlopen(req, data)
        data = json.loads(res.read())
        if (data['result'] != 'Success'):
            exit('API Error - Failed to register device')
        else:
            return data['details']
    except urllib2.HTTPError:
        exit('HTTP Error - Failed to register device')

def config(a, d):
    configdir = '/home/' + a.username + '/etc'
    uid = getpwnam(a.username).pw_uid

    if not os.path.exists(configdir):
        os.makedirs(configdir)

    # create deviceid file
    filename = configdir + '/deviceid'
    file = open(filename, 'w')
    file.write(d['id'])
    file.close()
    os.chown(filename, uid, -1)
    os.chmod(filename, 0600)

    # create devicekey file
    filename = configdir + '/devicekey'
    file = open(filename, 'w')
    file.write(d['key'])
    file.close()
    os.chown(filename, uid, -1)
    os.chmod(filename, 0600)

def setup_heartbeat(u):
    # Clone repository
    #subprocess.call(['git', 'clone', '.... something.

    # Setup cron
    script = '/home/' + u + '/heartbeat/heartbeat.py'
    file = open('/etc/cron.d/co2-heartbeat', 'w')
    file.write('* * * * * ' + u + ' python ' + script + "\n")
    file.close()

def setup_sync(u):
    script = '/home/' + u + '/readings/sync.py'
    file = open('/etc/cron.d/co2-sync', 'w')
    file.write('* * * * * ' + u + ' python ' + script + "\n")
    file.close()

def setup_readings(u):
    script = '/home/' + u + '/readings/readings.py'
    file = open('/etc/cron.d/co2-readings', 'w')
    file.write('* * * * * ' + u + ' python ' + script + "\n")
    file.close()

args = parse_options()

#install_packages(
#    ['git', 'dnsutils', 'python-serial', 'python-pip', 'python-dev'],
#    ['netifaces']
#)

setup_user(args.username)

data = register(args)

if (data != False):
    config(args, data)

setup_heartbeat(args.username)
setup_sync(args.username)
setup_readings(args.username)
