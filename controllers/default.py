# -*- coding: utf8 -*-
##Imports
import os, os.path
import random
import httplib, urllib,urllib2
import re
from xml.dom import minidom

"""
To Do:
-Add user settings page (lastfm info, play after search, default # for add more songs, default # for initial search, etc)
-Clean up code and add comments
-Add "Do you mean this artist?" If no results are found on first search
-Setup new layout for player with side bars for favorite stations and recently played
-Add User DB to add favorite songs and saved stations
-Look into how to like songs to lastfm and stream to lastfm (probably will require javascript)
"""

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
		return dict(printrows=searchlastfm, form=form)
	if artist and not song:
		session.printrows = []
		session.num = 15
		searchlastfm = mainvar.addArtistSongs(artist)
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
	print "Adding 5 Songs!"
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

def files():
	import scheduler
	form = SQLFORM.factory(Field('music_dir', label='File Directory', requires=IS_NOT_EMPTY()))
	if form.process().accepted:
		session.music_dir = form.vars.music_dir
		scan_dir.queue_task(dir_scan,pvars=dict(kind="*.mp3", dir=session.music_dir),timeout=5000)
#		os.path.walk(form.vars.music_dir, print_mp3, '*.mp3')
	grid = SQLFORM.grid(db.lastfm)
	return dict(form=form, grid=grid)
def dir_scan(dir, kind):
	os.path.walk(dir, print_mp3, kind)
class Main:
	def con_lastfm(self, apiMethod, artist, track=None):
		apiPath = "http://ws.audioscrobbler.com/2.0/?api_key=9ab0c1e4d83f21270341c70068d02d44"
		self.apiMethod = apiMethod
		self.artist = artist
		self.track = track
		if track:
			Base_URL = apiPath + apiMethod + "&artist=" + artist + "&track=" + track
		else:
			Base_URL = apiPath + apiMethod + "&artist=" + artist
		WebSock = urllib.urlopen(Base_URL)  # Opens a 'Socket' to URL
		WebHTML = WebSock.read()            # Reads Contents of URL and saves to Variable
		WebSock.close()                     # Closes connection to url
		return WebHTML
	def lastfmsearch(self, artist, track):
		self.artist = artist
		self.track=track
		WebHTML = mainvar.con_lastfm("&method=track.getsimilar",artist,track)
		similarTracks = mainvar.xmlparse(WebHTML, "similartracks")
		random.shuffle(similarTracks)
		countTracks = len(similarTracks)
		print "[LFM PLG(PM)] Count: " + str(countTracks)
		if countTracks == 0:
			return mainvar.addArtistSongs(artist)
		return similarTracks
	def addArtistSongs(self, artist):
		self.artist = artist
		WebHTML = mainvar.con_lastfm("&method=artist.getTopTracks",artist)
		similarTracks = mainvar.xmlparse(WebHTML, "toptracks")
		random.shuffle(similarTracks)
		artist = similarTracks[0][1].encode('utf8')
		song = similarTracks[0][0].encode('utf8')
		print "Searching for %s and %s from addArtistSongs" % (artist,song)
		return mainvar.addSongs(artist,song)
	def xmlparse(self, xml, xml_attrib):
		xml_x = minidom.parseString(xml)
		xml_lastfm = xml_x.getElementsByTagName("lfm")[0]
		xml_similarTracks = xml_lastfm.getElementsByTagName(xml_attrib)[0]
		xml_tracks = xml_similarTracks.getElementsByTagName("track")
		similarTracks = []
		for track in xml_tracks:
			try:
				xml_trackname = track.getElementsByTagName("name")[0].firstChild.data
			except Exception as detail:
				print detail
				xml_trackname = re.sub(r'\([^)]*\)', '', xml_trackname)  #deal with ('s
			xml_artist = track.getElementsByTagName("artist")[0]
			xml_artistname = xml_artist.getElementsByTagName("name")[0].firstChild.data
			try:
				xml_image = track.getElementsByTagName("image")[3].firstChild.data
			except:
#				print "Set to default image"
				xml_image = "http://www.clker.com/cliparts/6/c/1/4/1358105971891943396music_note1-md.png"
			try:
				similarTracks.append([xml_trackname, xml_artistname,  xml_image])
			except:
				print "Issue with %s - %s _ %s" % (xml_artistname, xml_trackname, xml_image)
		return similarTracks
	def addSongs(self, artist, song):
		self.artist = artist
		self.song = song
		if len(session.printrows) > session.num or len(session.printrows) == session.num:
			print "Starting over from addSongs"
			session.printrows = []
			mainvar.addSongs(artist,song)
		print "Searching %s - %s addSongs" % (artist, song) 
		for line in mainvar.lastfmsearch(artist,song):
			if len(line) == 3:
				similarTrackName = line[0]
				similarArtistName = line[1]
				artistArt = line[2]
				#Remove featured artists and special versions
				if " feat" in similarTrackName:
					similarTrackName=" feat".join(similarTrackName.split(' feat')[0:1])
				if "ft" in similarTrackName:
					similarTrackName=" ft".join(similarTrackName.split(' ft')[0:1])
				if " (" in similarTrackName:
					similarTrackName=" (".join(similarTrackName.split(' (')[0:1])
				if " [" in similarTrackName:
					similarTrackName=" [".join(similarTrackName.split(' [')[0:1])
				if " -" in similarTrackName:
					similarTrackName=" -".join(similarTrackName.split(' -')[0:1])
				
				try:
					similarTrackName = similarTrackName.replace("+"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
					similarArtistName = similarArtistName.replace("+"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
				except:
					similarTrackName[0] = similarTrackName.replace("+"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
					similarArtistName[0] = similarArtistName.replace("+"," ").replace("&quot","''").replace("'","''").replace("&amp;","and")
				row = db((db.lastfm.Artist.contains(similarArtistName.encode('utf8')))&(db.lastfm.Track.contains(similarTrackName.encode('utf8')))).select()
				if row and session.printrows==[]:
					session.printrows.append([row[0].Artist, row[0].Track, row[0].Dir, artistArt])
				if row and not session.printrows==[]:
					toadd=[row[0].Artist, row[0].Track, row[0].Dir, artistArt]
					if toadd not in session.printrows:
						session.printrows.append(toadd)
				if len(session.printrows) == session.num:
					break
		if len(session.printrows) == 0:
			mainvar.addArtistSongs(artist)
		if len(session.printrows) < session.num:
			print "Finding Similar"
			mainvar.findSimilar()
		return session.printrows
	def findSimilar(self):
		random.shuffle(session.printrows)
		artist = session.printrows[0][0]
		song = session.printrows[0][1]
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
