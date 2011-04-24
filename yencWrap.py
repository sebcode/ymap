import yenc, os, re, binascii, stat

SIZE_RE = re.compile(r"^.*? size=(\d+) .*$")

class yencWrap:

	def encode(self, inFilename, outFilename):
		try:
			fileIn = open(inFilename, 'r')
			fileOut = open(outFilename, 'w')

			crc = hex(binascii.crc32(open(inFilename,"r").read()))[2:]
			name = os.path.split(inFilename)[1]
			size = os.stat(inFilename)[stat.ST_SIZE]
			fileOut.write("=ybegin line=128 size=%d crc32=%s name=%s\r\n" % (size, crc, name) )
			encoded, crc = yenc.encode(fileIn, fileOut, size)
			fileOut.write("=yend size=%d crc32=%s\r\n" % (encoded, crc))
		finally:
			fileIn.close()
			fileOut.close()

