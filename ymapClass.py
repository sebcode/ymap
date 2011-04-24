from imaplib import *
import time, hashlib
import sys, rfc822, base64, yenc, os, re
from stat import *
from yencWrap import *

NAME_RE = re.compile(r"^.*? name=(.+?)\r\n$")
LINE_RE = re.compile(r"^.*? line=(\d{3}) .*$")
SIZE_RE = re.compile(r"^.*? size=(\d+) .*$")
CRC32_RE = re.compile(r"^.*? crc32=(\w+)")

class ymap:

	def connect(self, server, port, ssl, user, password, folder):
		if ssl:
			self.server = IMAP4_SSL(server, port)
		else:
			self.server = IMAP4(server, port)
		
		try:
			self.server.login(user, password);
		except IMAP4.error, e:
			print "Login error: %s" % e
			return False
		
		self.folder = folder

		try:
			t, d = self.server.select(folder, True)
			if t != 'OK':
				print "Could not select folder: %s (%s)" % (folder, d[0])
				return False
		except IMAP4.error, e:
			print "Could not select folder: %s (%s)" % (folder, e)
			return False

	def disconnect(self):
		self.server.logout()

	def list(self):
		try:
			code, msgList = self.server.fetch("1:*", "(BODY[HEADER.FIELDS (SUBJECT)] RFC822.SIZE)");
		except IMAP4.error, e:
			print "Could not fetch message list: %s" % e
			return False

		i = 0
		for msg in msgList:
			if (type(msg) == tuple):
				a, b = msg
				size = a.split(' ')[2]
				i = i + 1
				subject = msg[1].strip()[9:]
				try:
					decoded = subject.decode('hex').decode('base64')
				except:
					decoded = '';
				print "%i %s (%s bytes)" % (i, decoded, size)


	def get(self, num, downloadDir):
		code, msg = self.server.fetch(num, "(BODY[HEADER.FIELDS (SUBJECT)])");
		a, b = msg[0]
		f = b.strip()[9:].decode('hex').decode('base64')
		print "File %s requested" % f

		outFilename = "%s/%s" % (downloadDir, f)
		tmpFilename = "%s/%s.tmp" % (downloadDir, f)
		print "Downloading to %s" % tmpFilename
	
		if os.path.exists(outFilename) == True:
			print "File already exists: %s" % outFilename
			return False
		
		outfile = file(tmpFilename, 'w')
		code, msg = self.server.fetch(num, "(BODY[TEXT])");
		a, data = msg[0]
		outfile.write(data)
		outfile.flush()
		outfile.close()

		print "yDecoding..."

		file_in = open(tmpFilename, "r")
		while True:
			line = file_in.readline()
			if line.startswith("=ybegin "):
				try:
					name, size = NAME_RE.match(line).group(1), int(SIZE_RE.match(line).group(1))
					m_obj = CRC32_RE.match(line)
					if m_obj:
						head_crc = m_obj.group(1)
				except re.error, e:
					sys.stderr.write("err-critical: malformed =ybegin header\n")
					return False
				break
			elif not line:
				sys.stderr.write("err-critical: no valid =ybegin header found\n")
				return False

		file_out = open(outFilename, "w")
		try:
			dec, dec_crc = yenc.decode(file_in, file_out, size)
		except yenc.Error, e:
			sys.stderr.write(str(e) + '\n')
			return False

		head_crc = trail_crc = tmp_crc = ""
		garbage	= 0
		for line in file_in.read().split("\r\n"):
			if line.startswith("=yend "):
				try:	
					size = int( SIZE_RE.match(line).group(1) )
					m_obj = CRC32_RE.match(line)
					if m_obj:
						trail_crc = m_obj.group(1)
				except re.error, e:
					sys.stderr.write("err: malformed =yend trailer\n")
				break
			elif not line:
				continue
			else:
				garbage = 1
		else:
			sys.stderr.write("warning: couldn't find =yend trailer\n")
		if garbage:
			sys.stderr.write("warning: garbage before =yend trailer\n")
		if head_crc:
			tmp_crc = head_crc.lower()
		elif trail_crc:
			tmp_crc = trail_crc.lower()
		else:
			return True
		
		if cmp(tmp_crc, dec_crc):
			sys.stderr.write("err: header: %s dec: %s CRC32 mismatch\n" % (tmp_crc,dec_crc) )
			return False

		os.unlink(tmpFilename)


	def put(self, filename):
		print "Processing %s" % filename
		encName = filename.encode('base64').encode('hex')

		boundary = hashlib.md5("multipart %f" % time.time()).hexdigest()

		buf = []
		buf.append('From: nobody')
		buf.append('To: nobody')
		buf.append('Subject: %s' % encName)
		buf.append('Mime-Version: 1.0')
		buf.append('Content-Type: multipart/mixed; boundary="%s"' % boundary)
		buf.append('Content-Disposition: inline')
		buf.append('')
		buf.append('--%s' % boundary)
		buf.append('Content-Type: text/plain; charset=iso-8859-1')
		buf.append('')
		buf.append('')
		buf.append('')
		buf.append('--%s' % boundary)
		buf.append('Content-Type: application/octet-stream')
		buf.append('Content-Disposition: attachment; filename="data"')
		buf.append('Content-Transfer-Encoding: 8bit')
		buf.append('')

		print "yEncoding..."

		if os.access(filename, os.F_OK | os.R_OK) == False:
			print "Could not read %s" % filename
			return False

		eFilename = "tmpfile"

		y = yencWrap()
		y.encode(filename, eFilename)

		f = open(eFilename, 'r')
		buf.append(f.read())
		f.close()

		buf.append('')
		buf.append('--%s--' % boundary)
		
		print "Uploading..."
		self.server.append(self.folder, '', '', "\r\n".join(buf))

