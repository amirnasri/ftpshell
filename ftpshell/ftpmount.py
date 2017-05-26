from __future__ import print_function
from multiprocessing import Process
import os
import subprocess
import socket
from fuse import FUSE
from .ftp import ftp_session
from .ftp.ftp_parser import parse_response_error
from .ftp.ftp_session import login_error
from .ftp.ftp_fuse import FtpFuse
from .ftpshell import proc_input_args
from .ftpshell import cli_error


def ftp_mount(ftp, mountpoint, base_dir=None):
	"""Mount an ftp session on a mountpoint

	   Args:
	       ftp (FtpSession): An instance of FtpSession class which
	          already has a connection to an ftp-server.

	       mountpoint (str): Path to the directory whrere the ftp session
	       is to be mounted.

	       base_dir (str): Absolute path of the directory on the ftp server
	          to be mounted. If not provided, defaults to current server
	          directory.
	"""

	def run_fuse(mountpoint):
		#sys.stdout = sys.stderr = open(os.devnull, "w")
		print("fuse before")
		print("-------------%s" % ftp.shared_dict)
		try:
			mp_created = False
			if not os.path.exists(mountpoint):
				os.mkdir(mountpoint)
				mp_created = True
			mountpoint = os.path.abspath(mountpoint)
			# FUSE(FtpFuse(ftp), mountpoint, nothreads=True, foreground=True)

			FUSE(FtpFuse(ftp), mountpoint, nothreads=True, foreground=True)
		except RuntimeError:
			print("runtoirj*************")
			subprocess.call(["fusermount", "-u", mountpoint], shell=False)
			FUSE(FtpFuse(ftp), mountpoint, nothreads=True, foreground=True)
		finally:
			if mp_created:
				os.rmdir(mountpoint)


	fuse_process = Process(target=run_fuse, args=(mountpoint,))
	fuse_process.start()
	print("started fuse process, pid=%d" % fuse_process.pid)
	#self.fuse_process = fuse_process
	return fuse_process


def main():
	try:
		usage = 'Usage: ftpshell [username[:password]@]server[:port] mountpoint'
		server, port, server_path, username, password, mountpoint = proc_input_args(usage)
		ftp = ftp_session.FtpSession(server, port)
		ftp.login(username, password, server_path)
	except cli_error:
		return
	except login_error:
		print("Login failed.")
	except (socket.error, parse_response_error, ftp_session.network_error):
		ftp.close_server()
		print("Connection was closed by the server.")
	print("Running fuse! %s" % ftp.get_cwd())
	fuse_process = ftp_mount(ftp, mountpoint)
	fuse_process.join()

	'''
	pid = os.fork()
	if not pid:
		# Child process
		#print("Running fuse! %s" % ftp.get_cwd())
		#sys.stdout = sys.stderr = open(os.devnull, "w")
		mp_created = False
		if not os.path.exists(mountpoint):
			os.mkdir(mountpoint)
			mp_created = True
		mountpoint = os.path.abspath(mountpoint)
		#FUSE(FtpFuse(ftp, ftp.get_cwd()), mountpoint, nothreads=True, foreground=True)
		if mp_created:
			os.rmdir(mountpoint)
	'''

	# except BaseException as e:
	#    print("Received unpexpected exception '%s'. Closing the session." % e.__class__.__name__)


if __name__ == '__main__':
	main()
