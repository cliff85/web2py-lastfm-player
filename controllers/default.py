# -*- coding: utf-8 -*-
##Imports
import os, os.path
import random
import httplib, urllib,urllib2
import re


def index():
	form = SQLFORM.factory(Field('artist',
                                 label='Artist',
                                 requires=IS_NOT_EMPTY()),
							Field('track', label='Track'))
	if form.process().accepted:
		session.artist = form.vars.artist
		session.track = form.vars.track
		redirect(URL('play'))
	return dict(form=form)
def play():
	artist = session.artist
	song = session.get('track', None)
	addsongs = request.vars.addsongs
	form = SQLFORM.factory(Field('artist', label='Artist', requires=IS_NOT_EMPTY()),
							Field('track', label='Track'))
	if form.process().accepted:
		session.artist = form.vars.artist
		session.track = form.vars.track
		session.addsongs = None
		redirect(URL('play'))
	if addsongs:
		print "adding 5 songs"
		return dict(printrows=session.printrows, form=form)
	if artist and song:
		session.printrows = []
		session.num = 15
		searchlastfm = mainvar.addSongs(artist, song)
		print session.printrows
		return dict(printrows=searchlastfm, form=form)
	if artist and not song:
		session.printrows = []
		session.num = 15
		searchlastfm = mainvar.addArtistSongs(artist)
		print "Started from the bottom", searchlastfm
		return dict(printrows=searchlastfm, form=form)
	else:
		return "nothing found"
def stream():
    import os
    if os.path.exists(request.vars.path):
		print "trying to play", request.vars.path
		return response.stream(open(request.vars.path, 'rb'), chunk_size=4096)
    else:
        raise HTTP(404)
def lfm_like():
	return dict()
def lfm_add():
	print "STARTING......................."
	session.num += 5
	artist = session.get('artist', None)
	print "Adding artist: %s from lfm_add" % artist
	mainvar.addArtistSongs(artist)
	redirect(URL('play', vars=dict(addsongs=True)))
	return dict()
def lfm_new():
	print "Starting a new list>>>>>>>>>>>>>>>>>"
	session.printrows = []
	session.addsongs = None
	redirect(URL('play'))
def searchdb(Artist):
	artistlist = []
	for row in db(db.lastfm.Artist.like(Artist)).select():
		artistlist.append(row)
	return artistlist
def print_mp3(pattern, dir, files):
	from gluon.debug import dbg
	from fnmatch import fnmatch
	from mutagen.mp3 import MP3
	import sys
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
def files():
	form = SQLFORM.factory(Field('music_dir',
                                 label='File Directory',
                                 requires=IS_NOT_EMPTY()))
	if form.process().accepted:
		session.music_dir = form.vars.music_dir
		os.path.walk(form.vars.music_dir, print_mp3, '*.mp3')
	grid = SQLFORM.grid(db.lastfm)
	return dict(form=form, grid=grid)

class Main:
	def lastfmsearch(self, artist, track):
		self.artist = artist
		self.track=track
		apiPath = "http://ws.audioscrobbler.com/2.0/?api_key=9ab0c1e4d83f21270341c70068d02d44"
		apiMethod = "&method=track.getsimilar"
		# The url in which to use
		Base_URL = apiPath + apiMethod + "&artist=" + artist + "&track=" + track 
		#print Base_URL
		WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		WebSock.close()                     # Closes connection to url
		#print WebHTML
		similarTracks = re.findall('<track>.+?<name>(.+?)</name>.+?<artist>.+?<name>(.+?)</name>.+?</artist>.+?<image size="extralarge">(.+?)</image>.+?</track>', WebHTML, re.S)
		random.shuffle(similarTracks)
		countTracks = len(similarTracks)
		print "[LFM PLG(PM)] Count: " + str(countTracks)
		if countTracks == 0:
			return mainvar.addArtistSongs(artist)
		return similarTracks
	def addArtistSongs(self, artist):
		self.artist = artist
		apiPath = "http://ws.audioscrobbler.com/2.0/?api_key=9ab0c1e4d83f21270341c70068d02d44"
		apiMethod = "&method=artist.getTopTracks"
		# The url in which to use
		Base_URL = apiPath + apiMethod + "&artist=" + artist
		#print Base_URL
		WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		WebSock.close()                     # Closes connection to url
		#print WebHTML
		similarTracks = re.findall('<track.+?>.+?<name>(.+?)</name>.+?<artist>.+?<name>(.+?)</name>.+?</artist>.+?<image size="extralarge">(.+?)</image>.+?</track>', WebHTML, re.S)
		random.shuffle(similarTracks)
		print "from addArtistSongs: ", similarTracks
		artist = similarTracks[0][1]
		song = similarTracks[0][0]
		print "Searching for %s and %s from addArtistSongs" % (artist,song)
		return mainvar.addSongs(artist,song)
#		print "[LFM PLG(PM)] Count: " + str(countTracks)
	def addSongs(self, artist, song):
		self.artist = artist
		self.song = song
		print "if print rows greater than %s" % session.num
		if len(session.printrows) > session.num or len(session.printrows) == session.num:
			print "Starting over from addSongs"
			print len(session.printrows)
			session.printrows = []
			print session.printrows
			mainvar.addSongs(artist,song)
		print "Searching %s - %s and print rows is \n %s" % (artist, song, session.printrows) 
		for similarTrackName, similarArtistName, artistArt in mainvar.lastfmsearch(artist,song):
			similarTrackName = similarTrackName.replace("+"," ").replace("("," ").replace(")"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
			similarArtistName = similarArtistName.replace("+"," ").replace("("," ").replace(")"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
			row = db.executesql('SELECT * FROM lastfm Where Artist=? AND Track LIKE ?', (similarArtistName.decode('utf-8'), "%"+similarTrackName.decode('utf-8')+"%"))
#			print "addSongs searching for %s and %s" % (similarArtistName, similarTrackName)
			if row and session.printrows==[]:
				row[0] = row[0] + (artistArt,)
				print "adding %s from IF" % row
				session.printrows.append(row)
				print len(session.printrows)
				print "#I am after row!"
			if row and not session.printrows==[]:
				checklines = []
				for line in session.printrows:
					checklines.append(int(line[0][0]))
				if int(row[0][0]) not in checklines:
					row[0] = row[0] + (artistArt,)
					print "adding %s" % row
					session.printrows.append(row)
					print len(session.printrows)
			if len(session.printrows) == session.num:
				break
		if len(session.printrows) < session.num:
			print "Finding Similar"
			mainvar.findSimilar()
#		print mainvar.session.printrows
		return session.printrows
	def findSimilar(self):
		random.shuffle(session.printrows)
		print session.printrows
		artist = session.printrows[0][0][1]
		song = session.printrows[0][0][2]
		print "Searching for %s and %s" % (artist,song)
		mainvar.addSongs(artist,song)	
global mainvar
mainvar = Main()	
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
