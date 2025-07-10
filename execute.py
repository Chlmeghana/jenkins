import os
import time
import argparse
import getpass
import json
import sys
import signal
import errno
import logging
from py3270 import Emulator, CommandError
from functools import wraps
from execVM7 import main
# Return codes
ALL_FINE = 0
NO_LOGON_SCREEN = 1
WRONG_ID_OR_PW = 2
LOGON_FAILED = 3
ALREADY_LOGGED_ON = 4
SSL_HANDSHAKE_ERROR = 6
CONNECTION_FAILED = 7
LOGFILE_PATH_ERROR = 8
NO_CREDENTIALS = 10

CMSAPIExceptionMessages = {
    NO_LOGON_SCREEN: 'Logon screen not found.',
    WRONG_ID_OR_PW: 'LOGON unsuccessful. Incorrect userid and/or password.',
    LOGON_FAILED: 'LOGON unsuccessful.',
    ALREADY_LOGGED_ON: 'The user is already logged on.',
    SSL_HANDSHAKE_ERROR: 'SSL Handshake error. Try using --no-certificate-verification.',
    CONNECTION_FAILED: 'Could not connect to the host.',
    LOGFILE_PATH_ERROR: 'The provided logfile directory does not exist.',
    NO_CREDENTIALS: 'No credentials provided.'
}

HCP_ALREADY_LOGGED_ON = 'HCPLGA054E'

class TimeoutSignal(Exception):
    pass

class CMSAPIException(Exception):
    def __init__(self, error_code=None, additional_message=None):
        self.message = additional_message or ''
        if error_code is not None:
            self.message += CMSAPIExceptionMessages.get(error_code, '')
        super().__init__(self.message)

def print_to_terminal(message, quiet):
    if message and not quiet:
        print(message)

def timeout(seconds=300, error_message=os.strerror(errno.ETIMEDOUT)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutSignal(error_message)

        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)

        return wrapper
    return decorator

def file_parser(fileloc):
    if not fileloc:
        raise RuntimeError("No file name provided.")
    try:
        with open(os.path.normpath(fileloc)) as f:
            return f.readlines()
    except IOError as err:
        logging.error(err)
        return []

class expandedEmulator(Emulator):
    def send_pf10(self): self.exec_command(b'PF(10)')
    def send_pa1(self): self.exec_command(b'PA(1)')
    def send_clear(self): self.exec_command(b'CLEAR')

    def save_screen_string(self):
        s = self.exec_command(b'PrintText(string)')
        s.data = [line.decode('utf-8') for line in s.data]
        return s

    def return_screen(self):
        s = self.save_screen_string()
        for i, line in enumerate(s.data):
            print(f"{i} - {line}")
        return s

    def screen_parser(self, quiet=False):
        s = self.save_screen_string()
        non_empty = list(filter(None, s.data))
        if not quiet:
            for line in non_empty[:-1]:
                if line!= 80*" ":
                    print("-->",line)
        return non_empty[:-1]
    def screen_chug_spool(self,filename= None, quiet=False):
        print("screen of chug fun called")
        s = self.save_screen_string()
        non_empty = list(filter(None, s.data))
        if not quiet:
            for line in non_empty[:-2]:
                if line != 80*" ":
                    if filename in line:
                        print("lineeeee",line)
                        a=line.split(" ")
                        a=[item for item in a if item != '']
                        print(a)
                        if a[1].startswith("*"):
                            continue
                        print(a[1],a[2])
                        print("returning password")
                        self.exec_command(b'PF(3)')
                        self.exec_command(b'PF(3)')
                        return a[1],a[2]
                    print("---->",line)
        return non_empty[:-1]

class console:

    @timeout(seconds=120)
    def __init__(self, args_dict, username, password):
        self.args = args_dict
        self.__username = username
        self.__password = password
        host = f"y:{self.args['host']}" if self.args['no_certificate_verification'] else self.args['host']
        self.em = expandedEmulator(visible=self.args['console_on'])

        time.sleep(1)
        try:
            self.em.connect(host)
        except CommandError as err:
            raise CMSAPIException(
                error_code=SSL_HANDSHAKE_ERROR if 'SSLHandshake' in str(err) else CONNECTION_FAILED,
                additional_message=str(err))

        print_to_terminal('Connected to 3270 console.', self.args['quiet'])
        logging.info('Connection to 3270 console successful.')
        self.em.screen_parser(quiet=self.args['quiet'])

    def reset(self):
        self.em.send_pa1()
        self.em.send_string('i zcms')
        self.em.send_enter()
        time.sleep(1)
        self.em.send_enter()
        time.sleep(1)

        for _ in range(5):
            if self.findString('Ready;'):
                break
            time.sleep(1)
        logging.debug(self.em.screen_parser(quiet=self.args['quiet']))

    @timeout(seconds=60)
    def find_logon_screen(self):
        try:
            while not self.findString('USERID'):
                time.sleep(1)
            return ALL_FINE
        except TimeoutSignal:
            logging.error('Logon screen not found.')
            return NO_LOGON_SCREEN

    def logon(self):
        if self.find_logon_screen() != ALL_FINE:
            return NO_LOGON_SCREEN

        self.em.send_enter()
        self.em.send_string(f'logon {self.__username}')
        self.em.send_enter()
        time.sleep(1)
        self.em.send_string(self.__password)
        self.em.send_enter()
        time.sleep(1)

        if self.findString(HCP_ALREADY_LOGGED_ON):
            return ALREADY_LOGGED_ON
        if self.findString('incorrect userid and/or password'):
            return WRONG_ID_OR_PW
        if self.findString('LOGON unsuccessful'):
            return LOGON_FAILED

        print_to_terminal('LOGON successful.', self.args['quiet'])
        logging.info('LOGON successful.')
        self.reset()
        return ALL_FINE

    def findStatus(self, status):
        s = self.em.save_screen_string()
        return status in s.data[-1]

    def findString(self, string, status=None):
        s = self.em.save_screen_string()
        for line in s.data:
            if string in line:
                return self.findStatus(status) if status else True
        return False

    def execute_all(self, commands):
        for command in commands:
            self.execute_command(command.rstrip())
    def fun(self,filename):
        print("fun is called")
        self.em.send_clear()
        if not execfile:
            raise Exception('Empty filename.')
        sendCount=0
        f=0
        self.em.send_string("vmlink .dir servct:tools.chug ")
        self.em.send_enter()
        self.em.send_enter()
        self.em.send_string("vmlink .dir servct:tools.chug.hatt ")
        self.em.send_enter()
        self.em.send_enter()
        self.em.send_string("vmlink .dir servt2:tools.chug ")
        self.em.send_enter()
        self.em.send_enter()
        self.em.send_string("vmlink .dir servt2:tools.chug.hatt ")
        self.em.send_enter()
        self.em.send_enter()
        self.em.send_string("vmlink chugbuck 191 (pw read ")
        self.em.send_enter()
        self.em.send_enter()
        self.em.send_string(f"filel chug spool z")
        print("command sent")
        self.em.send_enter()
        count=0
        score=0
        c=0
        while True:

            time.sleep(1)
            screen_lines = self.em.screen_chug_spool(filename,quiet=self.args['quiet'])
            print("printing len of screen_lines",len(screen_lines))
            if len(screen_lines)==2:
                return screen_lines[0],screen_lines[1]
                
            if filename in screen_lines:
                print (screen_lines)
            s = self.em.save_screen_string()
            if self.findString('FILELIST'):
                self.em.send_pf(12)
                self.em.send_pf(11)
            print("=====================status===================",s.data[len(s.data) - 1])
            if self.findStatus('CP READ'):
                print("CP state;")
                self.em.send_clear()
                print("just cleared")
                self.em.exec_command(b'PA(1)')
                self.em.send_enter()
                while self.findStatus('VM READ'):
                    self.em.send_enter()
                    self.em.send_enter()
                    time.sleep(5)
                    print("waitttt")
                print("===============================================")
                    
            print("count============",count)
            if self.findString("1=Hlp 2=Add 3=Quit 4=Tab 5=SChg 6=? 7=Bkwd 8=Fwd 9=Rpt 10=R/L 11=Sp/Jn 12=Cursr"):
                print("next page is there")
                self.em.send_string(f"all/{execfile}")
                self.em.send_enter()
            if self.findString("Line=1 "):
                count+=1
            print("count============",count)
            if score==1:
                print("breaking")
                break
            if self.findString(execfile):
                print("bucket found")
                score=1
            logging.debug(screen_lines)
            if self.findStatus('VM READ'):
                self.em.send_string('b')
            if self.findString('CHUGD Test Results') :
                print("Execution succeeded")
                c+=1
                
            if self.findString('Ready'):
                print("Ready;")
                self.em.send_clear()
                print("===============================================")
                if c==1:
                    break
                continue
            if self.findString('CMS'):
                print("CMS state;")
                self.em.send_clear()
                while self.findStatus('VM READ'):
                    self.em.send_enter()
                    self.em.send_enter()
                    time.sleep(5)
                    print("waitttt")
                print("===============================================")
                if c==1:
                    break
                continue
            while self.findStatus('RUNNING'):
                time.sleep(3)
                if sendCount == 0:
                    self.em.send_string(f"filel chug spool z")
                    self.em.send_enter()
                    sendCount = 1
                    break
            while f==1 and self.findStatus('RUNNING'):
                print("Loading, Please wait.")
                time.sleep(30)    
            while f==1 and self.findStatus('VM READ'):
                self.em.send_enter()
                self.em.send_enter()
                time.sleep(1)
            if self.findStatus('MORE...') or self.findStatus('HOLDING'):
                self.em.send_clear()
                self.em.send_enter()
            if self.findString('Chug Test Results'):
                print("Execution succeeded")
                break
    
    def execute_command(self, command):
        self.em.send_clear()
        if not command:
            raise Exception('Empty command.')
        f=0
        self.em.send_string(command)
        self.em.send_enter()
        self.em.send_enter()
        while True:
            time.sleep(1)
            screen_lines = self.em.screen_parser(quiet=self.args['quiet'])
            s = self.em.save_screen_string()
            if self.findString('Executing:'):
                f=1
            if not self.findStatus('VM READ') or not self.findStatus('NOT ACCEPTED'):
                print("=====================status===================",s.data[len(s.data) - 1])
            logging.debug(screen_lines)
            if self.findStatus('VM READ'):
                self.em.send_string('b')
            if self.findString('CHUGD Test Results') or self.findString("failures") or self.findString(f"Bucket: {execfile} BUCKET *") or (f==1 and self.findString("Ready; T")):
                print("===================Execution succeeded==================")
                break
            if self.findString('Ready'):
                print("Ready;")
                self.em.send_clear()
                print("===============================================")
                continue
            if self.findString('CMS'):
                print("CMS state;")
                self.em.send_clear()
                continue
            while f==1 and self.findStatus('RUNNING'):
                print("Loading, Please wait.")
                time.sleep(30)    
            while f==1 and self.findStatus('VM READ'):
                self.em.send_enter()
                self.em.send_enter()
                time.sleep(1)
            if self.findStatus('MORE...') or self.findStatus('HOLDING'):
                self.em.send_clear()
                self.em.send_enter()
            if self.findString('Chug Test Results'):
                print("Execution succeeded")
                break

    def logoff(self):
        self.em.send_string('logoff')
        self.em.send_enter()
        time.sleep(1)

    def __del__(self):
        self.em.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CMS 3270 Automation Tool")
    parser.add_argument('abc', help='Provide abc as positional arg')
    parser.add_argument('abc', help='Provide abc as positional arg')
    lpar=sys.argv[2]
    execfile=sys.argv[3]
    print("========",lpar,execfile)
    address,filename=main(lpar,execfile)
    print(address,filename)
    
    parser.add_argument('--host',default=address)
    parser.add_argument('-u', '--username', default=None)
    parser.add_argument('-e', '--env_cred', nargs=2, metavar=('username', 'password'))
    parser.add_argument('-l', '--logfile', default=None)
    parser.add_argument('-t', '--traceback', action='store_true', default=False)
    parser.add_argument('--no-certificate-verification', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('-c', '--console-on', action='store_true', default=False)


    args = parser.parse_args()
    args_dict = vars(args)

    if not args.traceback:
        sys.tracebacklimit = 0

    if args.env_cred:
        u, p = args.env_cred
    elif args.username:
        u = args.username
        p = getpass.getpass()
    else:
        raise CMSAPIException(error_code=NO_CREDENTIALS)

    if args.logfile:
        logfile_path = os.path.expanduser(args.logfile)
        if not os.path.exists(os.path.dirname(logfile_path)):
            raise CMSAPIException(error_code=LOGFILE_PATH_ERROR)
        logging.basicConfig(filename=logfile_path, format='%(levelname)s:%(message)s', level=logging.DEBUG)
    
    try:
        c = console(args_dict, u, p)
        r = c.logon()
        if r != ALL_FINE:
            raise CMSAPIException(error_code=r)
        testid,testpass=c.fun(filename)
        print(testid,testpass,"===========")
        
        commands = [f"chugd {testid} {testpass} ({execfile}"]
        print(commands,"=============")
        c.execute_all(commands)
        c.logoff()
    except CMSAPIException as ex:
        print(f"Error: {ex}")
        exit(r if 'r' in locals() else 1)
    finally:
        if 'c' in locals():
            del c 
    exit(0)
    
    
