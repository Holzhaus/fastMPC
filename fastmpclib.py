from gi.repository import GObject, Gtk
import sqlite3, os
class Database(object):
	loaded = False
	def __init__(self, file, stats={'songs':-1}):
		self.db = sqlite3.connect(file)	
		self._cursor = self.db.cursor()
		rows = self._cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",('table','songs'))
		table_exists = rows.fetchall()[0][0]
		if table_exists:
			row = self._cursor.execute("SELECT COUNT(*) FROM songs")
			row = row.fetchone()
			if row[0] == int(stats['songs']):
				self.loaded = True
			
		if not self.loaded:
			self._cursor.execute('DROP TABLE IF EXISTS artists')
			self._cursor.execute('DROP TABLE IF EXISTS albums')
			self._cursor.execute('DROP TABLE IF EXISTS songs')
			self._cursor.execute('DROP TABLE IF EXISTS folders')
			self._cursor.execute('CREATE TABLE artists (id INTEGER NOT NULL PRIMARY KEY, name TEXT)')
			self._cursor.execute('CREATE TABLE albums (id INTEGER NOT NULL PRIMARY KEY, artistid INTEGER, name TEXT, compilation INTEGER)')
			self._cursor.execute('CREATE TABLE songs (id INTEGER NOT NULL PRIMARY KEY, albumid INTEGER, artist TEXT, disc INTEGER, track INTEGER, title TEXT, file TEXT, extension TEXT)')
			self._cursor.execute('CREATE TABLE folders (id INTEGER NOT NULL PRIMARY KEY, name TEXT, parent INTEGER, depth INTEGER, item TEXT, file INTEGER)')
			self.db.commit()
	# Parents
	def get_album_by_song_id(self,songid):
		self._cursor.execute('SELECT albumid FROM songs WHERE id=?',(songid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_disc_by_song_id(self,songid):
		self._cursor.execute('SELECT disc FROM songs WHERE id=?',(songid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_artist_by_album_id(self,albumid):
		self._cursor.execute('SELECT artistid FROM albums WHERE id=?',(albumid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	# Values
	def get_artist_name_by_id(self,artistid):
		print(artistid)
		self._cursor.execute('SELECT name FROM artists WHERE id=?',(artistid,))
		row = self._cursor.fetchone()
		print(row)
		if row:
			return row[0]
		return None
	def get_album_name_by_id(self,albumid):
		self._cursor.execute('SELECT name FROM albums WHERE id=?',(albumid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_song_name_by_id(self,songid):
		self._cursor.execute('SELECT songs.track, songs.title, songs.artist, albums.compilation FROM songs, albums WHERE songs.albumid=albums.id AND songs.id=?',(songid,))
		row = self._cursor.fetchone()
		if row:
			if row[3]:
				songname = "%s - %s" % (row[2], row[1])
			else:
				songname = "%s" % row[1]
			if row[0]:
				songname = "%i - %s" % (row[0], songname)
			return songname
		return None
	def get_song_filename_by_id(self,songid):
		self._cursor.execute('SELECT file FROM songs WHERE id=?',(songid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	# Positions
	def get_artist_position_by_id(self,artistid):
		return artistid-1
	def get_album_position_by_id(self,albumid):
		self._cursor.execute('SELECT b.id FROM a albums, b albums WHERE a.artistid=b.artistid AND a.id=? ORDER BY b.id ASC',(albumid,))
		rows = self._cursor.fetchall()
		if rows:
			albumpos = rows.index(albumid,)
			if albumpos:
				return albumpos
		return None
	def get_artist_position_by_album_id(self,albumid):
		artistid = self.get_artist_by_album_id(albumid)
		if artistid:
			return self.get_artist_position_by_id(artistid)
		return None
	def get_song_position_by_id(self,songid):
		self._cursor.execute('SELECT b.id FROM a songs, b songs WHERE a.disc=b.disc AND a.albumid=b.albumid AND a.id=? ORDER BY b.tracks ASC',(songid,))
		row = self._cursor.fetchall()
		if row:
			songpos = rows.index(songid,)
			if songpos:
				return songpos
		return None
	def get_album_position_by_song_id(self,songid):
		albumid = self.get_album_by_song_id(songid)
		if albumid:
			return self.get_album_position_by_id(songid)
		return None
	def get_artist_position_by_song_id(self,songid):
		self._cursor.execute('SELECT albums.artistid FROM songs, albums WHERE songs.albumid=albums.id AND songs.id=? ORDER BY albums.id ASC',(songid,))
		row = self._cursor.fetchone()
		if row:
			return get_artist_position_by_id(row[0])
		return None
	# Numbers
	def get_artist_number(self):
		self._cursor.execute('SELECT COUNT(*) FROM artists')
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_album_number_by_artist_id(self,artistid):
		self._cursor.execute('SELECT COUNT(*) FROM albums WHERE artistid=?',(artistid,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return none
	def get_disc_number_by_album_id(self,albumid):
		self._cursor.execute('SELECT disc, COUNT(DISTINCT disc) FROM songs WHERE albumid=? GROUP BY albumid',(albumid,))
		row = self._cursor.fetchone()
		if row:
			if row[0]:
				return row[1]
			else:
				return 0
		return None
	def get_song_number_by_album_id(self,albumid,discid=0):
		if discid:
			self._cursor.execute('SELECT COUNT(id) FROM songs WHERE albumid=? GROUP BY albumid',(albumid,))
		else:
			self._cursor.execute('SELECT COUNT(id) FROM songs WHERE albumid=? AND discid=? GROUP BY albumid',(albumid,discid))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return 0
	# Nth
	def get_nth_artist(self,n):
		self._cursor.execute('SELECT id FROM artists ORDER BY id ASC LIMIT 1 OFFSET ?',(n,))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_nth_album_by_artist_id(self, n, artistid):
		self._cursor.execute('SELECT id FROM albums WHERE artistid=? ORDER BY id ASC LIMIT 1 OFFSET ?',(artistid,n))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_nth_disc_by_album_id(self, n, albumid):
		self._cursor.execute('SELECT disc FROM songs WHERE albumid=? GROUP BY disc ORDER BY disc ASC LIMIT 1 OFFSET ?',(albumid,n))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	def get_nth_song_by_album_id(self, n, albumid, discid=0):
		if discid:
			self._cursor.execute('SELECT id FROM songs WHERE albumid=? AND disc=? ORDER BY disc ASC, track ASC, id ASC LIMIT 1 OFFSET ?',(albumid,discid,n))
		else:
			self._cursor.execute('SELECT id FROM songs WHERE albumid=? ORDER BY disc ASC, track ASC, id ASC LIMIT 1 OFFSET ?',(albumid,n))
		row = self._cursor.fetchone()
		if row:
			return row[0]
		return None
	# Iter
	def get_next(self,rowref_data):
		if not rowref_data:
			return None
		if rowref_data[0]==CollectionModel.ROWREF_ARTIST:
			self._cursor.execute('SELECT id FROM artists WHERE id>? ORDER BY id ASC LIMIT 1',(rowref_data[1],))
			row = self._cursor.fetchone()
			if row:
				return row[0]
		if rowref_data[0]==CollectionModel.ROWREF_ALBUM:
			self._cursor.execute('SELECT id FROM albums WHERE id>? ORDER BY id ASC LIMIT 1',(rowref_data[1],))
			row = self._cursor.fetchone()
			if row:
				return row[0]
		if rowref_data[0]==CollectionModel.ROWREF_DISC:
			self._cursor.execute('SELECT disc FROM songs GROUP BY disc ORDER BY disc ASC WHERE disc>? AND albumid=? LIMIT 1',(rowref_data[1][1],rowref_data[1][0]))
			row = self._cursor.fetchone()
			if row:
				return row[0]
		if rowref_data[0]==CollectionModel.ROWREF_SONG:
			self._cursor.execute('SELECT b.id FROM a songs, b songs ORDER BY b.disc ASC, b.track ASC, b.id ASC WHERE b.track=(a.track+1) AND a.disc=b.disc AND a.albumid=b.albumid AND a.id=? LIMIT 1',(rowref_data[1],))
			row = self._cursor.fetchone()
			if row:
				return row[0]
		return None

	def get_id_by_path(self, path):
		if not path:
			n = 0
			return self.get_nth_artist(int(n))
		elif isinstance(path,int):
			return self.get_nth_artist(path)			
		elif len(path)==1:
			return self.get_nth_artist(path[0])
		elif len(path)==2:
			artistid = self.get_nth_artist(path[0])
			if artistid:
				return self.get_nth_album_by_artist_id(path[1],artistid)
		elif len(path)==3:
			artistid = self.get_nth_artist(path[0])
			if artistid:
				albumid = self.get_nth_album_by_artist_id(path[1],artistid)
				if albumid:
					discid = self.get_nth_disc_by_album_id(path[2],albumid)
					if discid:
						return discid
					else:
						return self.get_nth_song_by_album_id(path[2],albumid)
		elif len(path)==4:
			artistid = self.get_nth_artist(path[0])
			if artistid:
				albumid = self.get_nth_album_by_artist_id(path[1],artistid)
				if albumid:
					discid = self.get_nth_disc_by_album_id(path[2],albumid)
					if discid:
						return self.get_nth_song_by_album_id(path[3],albumid, discid)
		return None						

	def parse(self, mpddata, config_compilations_artists=("Various Artists","Various","VA","V.A.","V. A.","Verschiedene Interpreten"),
				 config_compilations_folders=("Various Artists","Various","VA","V.A.","V. A.","Verschiedene Interpreten"),
				 config_artists_ignoreprefix=("The","Die"),
				 config_compilations_use=True,
				 config_compilations_artistname="Verschiedene Interpreten",
				 config_unknown_artistname="Unbekannter Interpret",
				 config_unknown_albumname="Unbekanntes Album",
				 config_unknown_songtitle="Unbekannter Titel",
				 config_artists_capitalize=True,
				 config_albums_capitalize=False,
				 config_songs_capitalize=False):


		folder_parents = {}
		c = self.db.cursor()
		albumartists = {}
		albums = {}
		for item in mpddata:
			# FIXME: What are we doing here?
			for tag, value in item.items():
				if isinstance(value, list):
					item[tag] = ", ".join(set(value))

			folder_file = 0 # Folderview Stuff
			if 'file' in item.keys():
				# Artists
				if 'artist' in item.keys():
					artist = str(item['artist'])
				else:
					artist = config_unknown_artistname
				# Albumartists
				if 'albumartist' in item.keys():
					albumartist = str(item['albumartist'])
				else:
					albumartist = artist
				
				artist = artist.strip()
				albumartist = albumartist.strip()

				if config_artists_capitalize:
					artist = ' '.join(word.capitalize() for word in artist.split())
					albumartist = ' '.join(word.capitalize() for word in albumartist.split())

				if config_artists_ignoreprefix:
					for ignore in config_artists_ignoreprefix:
						if artist.lower().startswith("%s " % ignore.lower()):
							artist = "%s, %s" % (artist[len(ignore):].strip(),ignore)
						if albumartist.lower().startswith("%s " % ignore.lower()):
							albumartist = "%s, %s" % (albumartist[len(ignore):].strip(),ignore)
				artist = str(artist)
				albumartist = str(albumartist)

				# Compilations
				compilation = 0
				if config_compilations_use:
					if config_compilations_artists:
						if artist in config_compilations_artists:
							compilation = 1
				
					if config_compilations_folders:
						if str(str(str(item['file']).split("/")[0]).split("\\")[0]).strip() in config_compilations_folders:
							compilation = 1

				if compilation:
					albumartist_id = 0
				elif albumartist in albumartists.keys():
					albumartist_id = albumartists[albumartist]
				else:
					c.execute('INSERT INTO artists (name) VALUES (?)', (albumartist,))
					albumartist_id = c.lastrowid
					albumartists[albumartist] = albumartist_id
				if not albumartist_id in albums.keys():
					albums[albumartist_id] = {}
				
				# Albums
				if 'album' in item.keys():
					album = str(item['album'])
				else:
					album = config_unknown_albumname

				if config_albums_capitalize:
					album = ' '.join(word.capitalize() for word in album.split())

				if album in albums[albumartist_id].keys():
					album_id = albums[albumartist_id][album]
				else:					
					c.execute('INSERT INTO albums (artistid, name, compilation) VALUES (?,?,?)', (albumartist_id, album, compilation))
					album_id = c.lastrowid
					albums[albumartist_id][album] = album_id

				# Discs
				if 'disc' in item.keys():
					try:
						disc = int(str(str(item['disc']).split("/")[0]).split("-")[0])
					except Exception:
						disc = 0
				else:
					disc = 0

				# Songs
				track = 0
				file = str(item['file'])
				if 'title' in item.keys():
					title = str(item['title'])
					if config_songs_capitalize:
						title = ' '.join(word.capitalize() for word in title.split())
				else:
					title = config_unknown_songtitle
				if 'track' in item.keys():
					# Sometimes the track attribute contains something like "2/15" (Track 2 of 15).
					# We want only the first number, so we strip out the rest
					try:
						track = int(str(str(item['track']).split("/")[0]).split("-")[0])
					except Exception:
						track = 0

				try:
					extension = file.rsplit(".",1)[1].lower()
				except Exception:
					extension = ""

				c.execute('INSERT INTO songs (albumid, artist, disc, track, title, file, extension) VALUES (?,?,?,?,?,?,?)', (album_id, artist, disc, track, title, file, extension))
				
				# Folderview stuff
				folder_item = str(item['file'])
				folder_file = 1
	 		# More Folderview stuff
			elif 'directory' in item.keys():
				folder_item = str(item['directory'])

			folder_name = os.path.basename(folder_item)
			folder_currentpath =  os.path.dirname(folder_item)
			folder_depth = len(folder_currentpath.split(os.sep))
			folder_parent = None
			if folder_currentpath in folder_parents.keys():
				folder_parent = folder_parents[folder_currentpath]

			c.execute('INSERT INTO folders (name, parent, depth, item, file) VALUES (?,?,?,?,?)', (folder_name, folder_parent, folder_depth, folder_item, folder_file))
			if not folder_file and not folder_item in folder_parents.keys():
				folder_parents[folder_item] = c.lastrowid
			
		self.db.commit()
		c.close()

class CollectionModel(GObject.Object, Gtk.TreeModel):
	STAMP = 0
	NUM_COL = 4
	(ROWREF_ARTIST, ROWREF_ALBUM, ROWREF_DISC, ROWREF_SONG) = (1,2,3,4)
	COL_TYPES = (str,str,str,str)
	COL_NAMES = ("name",
		     "file",
		     "icon",
		     "sort")
	# rowrefs are tuples with 2 elements:
	# 	1 = type (Artist, Album, Disc, Song)
	#       2 = ID (if type is ROWREF_DISC, ID is a tuple of albumid and discid)
	def __init__(self, db):
		GObject.GObject.__init__(self)
		self.db = db
	
	def do_get_column_names(self):
		return self.COL_NAMES[:]

	def do_get_flags(self):
		return Gtk.TreeModelFlags.ITERS_PERSIST

	def do_get_n_columns(self, *data):
		return len(self.COL_TYPES)

	def do_get_column_type(self, n):
		#return CollectionModel.COL_TYPES[n]
		return str

	def do_get_iter_first(self):
		return self.do_get_iter(Gtk.TreePath(0))

	def do_get_iter(self, path):
		print("do get iter", path, type(path))
		path = path.get_indices()
		rowrefid = self.db.get_id_by_path(path)
		t = Gtk.TreeIter()
		t.stamp = self.STAMP
		if not path or isinstance(path,int) or len(path) == 1:
			t.user_data = (CollectionModel.ROWREF_ARTIST, rowrefid)
		elif len(path) == 2:
			t.user_data = (CollectionModel.ROWREF_ALBUM, rowrefid)
		elif len(path) == 3:
			if isinstance(rowref,tuple):
				t.user_data = (CollectionModel.ROWREF_DISC, rowrefid)
			else:
				t.user_data = (CollectionModel.ROWREF_SONG, rowrefid)
		elif len(path) == 4:
			t.user_data = (CollectionModel.ROWREF_SONG, rowrefid)
		else:
			raise InvalidColumnError
		return (True, t)

	def do_get_path(self, rowref):
		print("do get_path", rowref)
		if not rowref:
			return Gtk.TreePath(0)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ARTIST:
			artistpos = self.db.get_artist_position_by_id(rowref.user_data[1])
			if artistpos:
				return Gtk.TreePath(artistpos,)
				
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			albumpos = self.db.get_albuetm_position_by_id(rowref.user_data[1])
			if albumpos:
				artistpos = self.db.get_artist_position_by_album_id(rowref.user_data[1])
				if artistpos:
					return Gtk.TreePath(artistpos, albumpos)
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			discpos = (rowref.user_data[1][1]-1)
			if discpos:
				albumpos = self.db.get_album_position_by_id(rowref.user_data[1][1])
				if albumpos:
					artistpos = self.db.get_artist_position_by_album_id(rowref.user_data[1])
					if artistpos:
						return Gtk.TreePath(artistpos, albumpos, discpos)
		elif rowref.user_data[0] == CollectionModel.ROWREF_SONG:
			songpos = self.db.get_song_position_by_id(rowref.user_data[1])
			if songpos:
				discid = self.db.get_disc_by_song_id(rowref.user_data[1])
				albumpos = self.db.get_album_position_by_song_id(rowref.user_data[1])
				if albumpos:
					artistpos = self.db.get_artist_song_by_id(rowref.user_data[1])
					if artistpos:
						if discid:
							return Gtk.TreePath(artistpos, albumpos, (discpos-1), songpos)
						else:
							return Gtk.TreePath(artistpos, albumpos, songpos)
		return Gtk.TreePath(0)

	def do_get_value(self, rowref, column):
		print("do get_value" , rowref, column)
		return "test"
		"""print("do_get_value",rowref)
		if not rowref or not rowref.user_data:
			print("Damn it, something went wrong!")
			return "ERROR" # This should NEVER happen
		elif rowref.user_data[0] == CollectionModel.ROWREF_ARTIST:
			if column == 0:
				return self.db.get_artist_name_by_id(rowref.user_data[1])
			elif column == 1:
				return ""
			elif column == 2:
				return str(Gtk.STOCK_ORIENTATION_PORTRAIT)
			elif column == 2:
				return ""
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			if column == 0:
				return self.db.get_album_name_by_id(rowref.user_data[1])
			elif column == 1:
				return ""
			elif column == 2:
				return str(Gtk.STOCK_CDROM)
			elif column == 2:
				return ""
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			if column == 0:
				return "CD %s" % str(rowref.user_data[1][1])
			elif column == 1:
				return ""
			elif column == 2:
				return ""
			elif column == 2:
				return ""
		elif rowref.user_data[0] == CollectionModel.ROWREF_SONG:
			if column == 0:
				return self.db.get_song_name_by_id(rowref.user_data[1])
			elif column == 1:
				return self.db.get_song_filename_by_id(rowref.user_data[1])
			elif column == 2:
				return ""
			elif column == 3:
				return ""

		raise InvalidColumnError(column)
		return "Error"""

	def do_iter_next(self, rowref):
		print('iter next', rowref)
		if not rowref or not rowref.user_data:
			return (False, None)
		t = Gtk.TreeIter()
		t.stamp = self.STAMP
		t.user_data = (rowref.user_data[0], self.db.get_next(rowref.user_data))
		return (True, t)

	"""def do_iter_next(self, rowref):
		print('iter previous', rowref)
		raise NotImplementedError("I'm feeling lazy right now...")
		if not rowref or not rowref.user_data:
			return (False, None)
		t = Gtk.TreeIter()
		t.stamp = self.STAMP
		t.user_data = (rowref.user_data[0], self.db.get_next(rowref.user_data))
		return (True, t)"""

	def do_iter_children(self, rowref):
		"""if not rowref or not rowref:
			return self.db.get_nth_artist(0)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ARTIST:
			albumid = self.db.get_nth_album_by_artist_id(rowref.user_data[1])
			if albumid:
				return (CollectionModel.ROWREF_ALBUM, albumid)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			discid = self.db.get_nth_disc_by_album_id(rowref.user_data[1])
			if discid:
				return (CollectionModel.ROWREF_DISC, discid)
			else:
				songid = self.db.get_nth_song_by_album_id(rowref.user_data[1])
				if songid:
					return (CollectionModel.ROWREF_SONG, songid)
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			songid = self.db.get_nth_song_by_album_id(rowref.user_data[1][0], rowref.user_data[1][1])
			if songid:
				return (CollectionModel.ROWREF_SONG, songid)
		return None"""
		return self.iter_nth_child(self, rowref, 0)

	def do_iter_has_child(self, rowref):
		print ('has_child', rowref)
		if not rowref or not rowref.user_data:
			return True
		elif rowref.user_data[0] == CollectionModel.ROWREF_SONG:
			return False
		else:
			return True

	def do_iter_n_children(self, rowref):
		if not rowref:
			return self.db.get_artist_number()
		elif rowref.user_data[0] == CollectionModel.ROWREF_ARTIST:
			return self.db.get_album_number_by_artist_id(rowref.user_data[1])
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			discnumber = self.db.get_disc_number_by_album_id(rowref.user_data[1])
			if discnumber:
				return discnumber
			else:
				return self.db.get_song_number_by_album_id(rowref.user_data[1])
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			return self.db.get_song_number_by_album_id(rowref.user_data[1][0], rowref.user_data[1][1])
		return 0

	def do_iter_nth_child(self, rowref, n):
		t = Gtk.TreeIter()
		t.stamp = self.STAMP
		if not rowref:
			return (False, None)
		elif not rowref.user_data:
			artistid = self.db.get_nth_artist(n)
			if artistid:
				t.user_data = (CollectionModel.ROWREF_ARTIST, artistid)
				return (True, t)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ARTIST:
			albumid = self.db.get_nth_album_by_artist_id(n, rowref.user_data[1])
			if albumid:
				t.user_data = (CollectionModel.ROWREF_ALBUM, albumid)
				return (True, t)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			discid = self.db.get_nth_disc_by_album_id(n, rowref.user_data[1])
			if discid:
				t.user_data = (CollectionModel.ROWREF_DISC, (albumid, discid))
				return (True, t)
			else:
				songid = self.db.get_nth_song_by_album_id(n, rowref.user_data[1])
				if songid:
					t.user_data = (CollectionModel.ROWREF_SONG, songid)
					return (True, t)
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			songid = self.db.get_nth_song_by_album_id(n, rowref.user_data[1][0], rowref.user_data[1][1])
			if songid:
				t.user_data = (CollectionModel.ROWREF_SONG, songid)
				return (True, t)
		return (False, None)

	def do_iter_parent(self, rowref):
		t = Gtk.TreeIter()
		t.stamp = self.STAMP
		if not rowref:
			return (False, None)
		if rowref.user_data[0] == CollectionModel.ROWREF_SONG:
			albumid = self.db.get_album_by_song_id(rowref.user_data[1])
			discid = self.db.get_disc_by_song_id(rowref.user_data[1])
			if discid:
				t.user_data = (CollectionModel.ROWREF_DISC, (albumid, discid))
				return (True, t)
			else:
				t.user_data = (CollectionModel.ROWREF_ALBUM, albumid)
				return (True, t)
		elif rowref.user_data[0] == CollectionModel.ROWREF_ALBUM:
			t.user_data = (CollectionModel.ROWREF_ARTIST, self.db.get_artist_by_album_id(rowref.user_data[1]))
			return (True, t)
		elif rowref.user_data[0] == CollectionModel.ROWREF_DISC:
			t.user_data = (CollectionModel.ROWREF_ALBUM, rowref.user_data[1][0])
			return (True, t)
		return (False, None)
	def do_ref_node(self, treeiter):
		print("ref node")
	def do_unref_node(self, treeiter):
		print("unref node")
