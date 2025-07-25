#!/usr/bin/env python3
import argparse
import datetime
import ftplib
import getpass
import logging
import os
import re
import shlex
import subprocess
import sys
import time

from ftplib import FTP_TLS
from tempfile import TemporaryFile


desc = """
Sync a git controlled folder to a z/VM ftp minidisk or SFS directory.
It supports the following environment variables as input:
FTP_HOST
FTP_USER
FTP_PASSWORD
FTP_DIR
"""
parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
parser.add_argument("-d", "--debug", action="store_true", help="debug mode")
parser.add_argument("-f", "--force", action="store_true", help="force, ignore change date and transfer all")
parser.add_argument("-D", "--delete", action="store_true", help="delete files on VM host")
parser.add_argument("--dry", action="store_true", help="Only run into try mode, not changing any files on the host")
parser.add_argument("--host", help="FTP Host")
parser.add_argument("--user", help="FTP User")
parser.add_argument("-p", "--password", action="store_true", help="Prompt for FTP password")
parser.add_argument("--dir", help="FTP directory, minidisk or SFS directory")
parser.add_argument("--delta", type=int, default=10, help="Set the maximum time delta where files should be transfered even if newer on the host, in seconds")
parser.add_argument("folders", nargs='+', help="files to format/check")
args = parser.parse_args()


log_format = '%(levelname)s:%(message)s'

if args.debug:
	logging.basicConfig(format=log_format, level=logging.DEBUG)
elif args.verbose:
	logging.basicConfig(format=log_format, level=logging.INFO)
else:
	logging.basicConfig(format=log_format, level=logging.WARNING)

ftp_host = None
ftp_user = None
ftp_password = None
ftp_disk = None

if 'FTP_HOST' in os.environ:
	ftp_host = os.environ['FTP_HOST']

if 'FTP_USER' in os.environ:
	ftp_user = os.environ['FTP_USER']

if 'FTP_PASSWORD' in os.environ:
	ftp_password = os.environ['FTP_PASSWORD']

if 'FTP_DIR' in os.environ:
	ftp_disk = os.environ['FTP_DIR']


if args.host is not None:
	ftp_host = args.host

if args.user is not None:
	ftp_user = args.user

if args.dir is not None:
	ftp_disk = args.dir

if ftp_host is None or ftp_user is None or ftp_disk is None:
	logging.error("Host, User or Disk have not been specified via parameter or environmental variables")
	sys.exit(1)

if ftp_password is None or args.password:
	ftp_password = getpass.getpass()

max_delta = args.delta

def get_host_time_delta(ftp):
	file = TemporaryFile()
	file.write("Time Test".encode('ascii'))
	file.seek(0)

	lines = []
	try:
		# Store temporary file on ftp host
		ftp.storlines("STOR TIME.TEST", file)

		# Retrieve directory contents
		ftp.retrlines('LIST',lines.append)

		# Remove temporary file
		ftp.delete("TIME.TEST")
	except ftplib.all_errors as err:
		logging.error("Error while determining ftp time offset:\n" + str(err))
		ftp.quit()
		sys.exit(1)
	file.close()

	# Loop through files to find TIME.TEST
	for line in lines:
		# Split filel output into different file attributes
		try:
			f_name, f_type, f_format, f_lrecl, f_records, f_blocks, f_date, f_time, f_rest = re.sub(' +', ' ',line).split(" ", 8)
		except ValueError as err:
			logging.debug("Can't identify file: " + line)
			continue

		if f_name == "TIME" and f_type == "TEST":

			# Expecting date/time in this format: 2018-11-08 06:02:06
			host_time = time.strptime(f_date + " " + f_time,"%Y-%m-%d %H:%M:%S")

			# Calculate delta in seconds to host time
			delta = int(time.mktime(host_time)-time.mktime(time.localtime()))
			logging.debug('Time difference to host: ' + str(delta))
			return delta
	logging.error("Unable to find TEST.TIME file on host")
	raise Exception("Unable to find TEST.TIME file on host")


def get_git_change_timestamp(folder, file):
	output = subprocess.run('cd ' + folder + ' && git log -1 --date=unix --format="%ad" -- ' + shlex.quote(file), shell=True, stdout=subprocess.PIPE, encoding='utf-8')
	#print(output)
	try:
		timestamp = int(output.stdout.strip())
	except ValueError:
		return None
	return timestamp


host_files_processed = False
host_file_list = None
host_files = []
def get_host_change_timestamp(ftp, file):
	global host_files_processed
	global host_file_list
	global host_files

	if host_files_processed == False:
		try:
			host_files_processed = True
			host_file_list = []
			ftp.retrlines('LIST',host_file_list.append)

			for host_file in host_file_list:
				try:
					f_name, f_type, f_format, f_lrecl, f_records, f_blocks, f_date, f_time, f_rest = re.sub(' +', ' ',host_file).split(" ", 8)
					host_files.append(f_name + "." + f_type)
				except ValueError as err:
					logging.debug("Can't identify file: " + host_file)
					continue

		except ftplib.all_errors as err:
			logging.debug('Coudn\'t obtain file list, assuming empty dir: ' + str(err))
			return None

	for host_file in host_file_list:
		try:
			f_name, f_type, f_format, f_lrecl, f_records, f_blocks, f_date, f_time, f_rest = re.sub(' +', ' ',host_file).split(" ", 8)
		except ValueError as err:
			logging.debug("Can't identify file: " + host_file)
			continue
		if f_name + "." + f_type == file:
			timestamp = time.mktime(time.strptime(f_date + " " + f_time,"%Y-%m-%d %H:%M:%S"))
			return int(timestamp)
	return None



################################################################################
#
# main function entry
#
################################################################################


# Connecto to FTP host
try:
	ftp = FTP_TLS(ftp_host)
	ftp.connect()
	ftp.login(ftp_user, ftp_password)
	ftp.prot_p()
	ftp.cwd(ftp_disk)
except ftplib.all_errors as err:
	print("Error while connectiong to ftp: ", err)
	ftp.quit()
	sys.exit(1)

# Get local file list

time_delta = get_host_time_delta(ftp)
all_files = []

for folder in args.folders:

	logging.info("Processing local folder " + folder)

	try:
		local_files = os.listdir(folder)
		all_files.extend(local_files)

	except FileNotFoundError as err:
		logging.warning("Unable to open folder " + folder)
		local_files = []

	transferred = 0


	# Upload newer local files
	for file in local_files:

		# Check if file name/type longer than 8 characters
		if "." in file:
			f_name, f_type = file.split(".",2)
			if len(f_name) > 8 or len(f_type) > 8:
				logging.warning("File " + str(file) + " has a file name or typer longer than 8 characters")

		# Get change times
		local_time = get_git_change_timestamp(folder, file)
		host_time = get_host_change_timestamp(ftp, file)

		# Skip local files not under version control
		if local_time is None:
			logging.info("Skipping local file " + file + ", not under version control")
			continue

		if args.force or host_time is None or (local_time + time_delta - host_time) > -max_delta:
			if host_time is None:
				logging.info("File " + file + " not on host, transferring")
			elif args.force:
				logging.info("Forceing transfer of file " + file)
			else:
				logging.info("File " + file + " is " + str(local_time + time_delta - host_time) + " seconds older on host, transferring")
			try:
				file_p = open(folder + "/" + file,"rb")
				if not args.dry:
					if f_type.upper() == "PDF":
						ftp.storbinary("STOR" + file, file_p)
					else:
						ftp.storlines("STOR " + file, file_p)
					transferred += 1
				file_p.close()
				if not args.dry:
					logging.info("File " + file + " has been transferred")
				else:
					logging.info("File " + file + " would be transferred")
			except ftplib.all_errors as err:
				logging.error("Could not transfer file " + file + ": " + str(err))

		else:
			logging.info("File " + file + " is " + str(abs(local_time + time_delta - host_time)) + " seconds newer on host, skipping")
	logging.info("Transferred " + str(transferred) + " newer files to host")

# Delete host files not present locally
deleted = 0
if args.delete:
	for host_file in host_files:
		if host_file not in all_files:
			if not args.dry:
				try:
					ftp.delete(host_file)
					logging.info("File " + host_file + " has been deleted")
					deleted += 1

				except ftplib.all_errors as err:
					logging.error("Could not delete file " + host_file + ": " + err)
			else:
				logging.info("File " + host_file + " would have been deleted")

logging.info("Deleted " + str(deleted) + " files from host that did not exist locally")
ftp.quit()
