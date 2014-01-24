import os, os.path

def dir_scan(dir, kind):
	os.path.walk(dir, print_mp3, kind)

def print_mp3(pattern, dir, files):
	from gluon.debug import dbg
	from fnmatch import fnmatch
	from mutagen.mp3 import MP3
	import sys
	print "Starting looking for %s %s %s" %(pattern,dir, files)
	row = db.lastfm
	for filename in files:
		if not row(Dir=os.path.join(dir, filename)):
			if fnmatch(filename, pattern):
				audio = MP3(os.path.join(dir, filename))
				try:
					track = audio['TIT2']
					artist = audio['TPE1']
				except:
					print "Missing key:"
					print os.path.join(dir, filename)
				try:
					db.lastfm.insert(Artist=artist, Track=track, Dir=os.path.join(dir, filename))
					print "adding %s" % os.path.join(dir, filename)
				except:
					e = sys.exc_info()[0]
					print "ERROR: %s" % e
					print os.path.join(dir, filename)
	db.commit()
from gluon.scheduler import Scheduler 
scan_dir = Scheduler(db, dict(dir_scan=dir_scan))
#scheduler = Scheduler(db)