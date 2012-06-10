#!/usr/bin/env python3
#
# fastMPC - Python MPD client
#
# Copyright (C) 2012  Jan Holthuis <jan.holthuis@ruhr-uni-bochum.de>
#
# fastMPC is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fastMPC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fastMPC. If not, see <http://www.gnu.org/licenses/>.
#

import mpd, math, sys, os, json, threading, configparser
from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, Notify

APPNAME = "fastMPC"
APPVERSION = 0.02

class PollerError(Exception):
	"""Fatal error in poller."""
	pass

# Custom wrapper class for the mpdclient
class MPDPoller(object):
	def __init__(self, host="localhost", port=6600, password=None, timeout=10):
		self._host = host
		self._port = port
		self._password = password
		self._timeout = timeout
		self._client = mpd.MPDClient()
		self.mpd_version = ""
		Notify.init(APPNAME.lower())

	def connect(self):
		try:
			self._client.connect(self._host, self._port, self._timeout)
		# Catch socket errors
		except IOError as e:
			errno, strerror = e.args
			raise PollerError("Could not connect to '%s': %s" % (self._host, strerror))
		# Catch all other possible errors
		# ConnectionError and ProtocolError are always fatal.  Others may not
		# be, but we don't know how to handle them here, so treat them as if
		# they are instead of ignoring them.
		except Exception as e:
			raise PollerError("Could not connect to '%s': %s" % (self._host, e))
		else:
			if self._password:
				try:
					self._client.password(self._password)
	
				# Catch errors with the password command (e.g., wrong password)
				except CommandError as e:
					raise PollerError("Could not connect to '%s': password commmand failed: %s" % (self._host, e))
	
				# Catch all other possible errors
				except (mpd.MPDError, IOError) as e:
					raise PollerError("Could not connect to '%s': error with password command: %s" % (self._host, e))
		
			self.mpd_version = self._client.mpd_version

	def disconnect(self):
		# Try to tell MPD we're closing the connection first
		try:
			self._client.close()

		# If that fails, don't worry, just ignore it and disconnect
		except (mpd.MPDError, IOError, TypeError):
			pass

		try:
			self._client.disconnect()

		# Disconnecting failed, so use a new client object instead
		# This should never happen.  If it does, something is seriously broken,
		# and the client object shouldn't be trusted to be re-used.
		except (mpd.MPDError, IOError, TypeError):
			self._client = mpd.MPDClient()
	def _runMPDCommand(self, polling_target, user_data=""):
		if polling_target == "currentsong":
			return self._client.currentsong()
		elif polling_target == "stats":
			return self._client.stats()
		elif polling_target == "status":
			return self._client.status()
		elif polling_target == "listplaylists":
			return self._client.listplaylists()
		elif polling_target == "playlistinfo":
			return self._client.playlistinfo()
		elif polling_target == "clear":
			return self._client.clear()
		elif polling_target == "load":
			return self._client.load(user_data)
		elif polling_target == "add":
			print("add",user_data)
			return self._client.add(user_data)
		elif polling_target == "playid":
			return self._client.playid(user_data)
		elif polling_target == "listallinfo":
			return self._client.listallinfo()
		elif polling_target == "play":
			return self._client.play()
		elif polling_target == "pause":
			return self._client.pause()
		elif polling_target == "stop":
			return self._client.stop()
		elif polling_target == "next":
			return self._client.next()
		elif polling_target == "previous":
			return self._client.previous()
		elif polling_target == "setvol":
			return self._client.setvol(user_data)
		elif polling_target == "repeat":
			return self._client.repeat(int(user_data))
		elif polling_target == "random":
			return self._client.random(int(user_data))
		elif polling_target == "shuffle":
			return self._client.shuffle(user_data)
		elif polling_target == "remove":
			return self._client.remove(user_data)
		elif polling_target == "save":
			return self._client.save(user_data)

	def _poll(self, polling_target, user_data=""):
		try:
			result = self._runMPDCommand(polling_target, user_data)

		except (mpd.ProtocolError):
			# Doesn't matter
			result = False
		# Couldn't get the current song, so try reconnecting and retrying
		except (mpd.MPDError, IOError):
			# No error handling required here
			# Our disconnect function catches all exceptions, and therefore
			# should never raise any.
			self.disconnect()

			try:
				self.connect()

			# Reconnecting failed
			except PollerError as e:
				raise PollerError("Reconnecting failed: %s" % e)

			try:
				result = self._runMPDCommand(polling_target, user_data)

			# Failed again, just give up
			except (mpd.MPDError, mpd.ProtocolError, IOError) as e:
				raise PollerError("Couldn't execute MPD Command %s(%s): %s" % (polling_target, user_data, e))
				result = False
		# Hurray!  We got the current song without any errors!
		return result
	# Dummy Functions
	def currentsong(self):
		return self._poll("currentsong")
	def stats(self):
		print("stats")
		return self._poll("stats")
	def status(self):
		return self._poll("status")
	def listplaylists(self):
		return self._poll("listplaylists")
	def playlistinfo(self):
		return self._poll("playlistinfo")
	def clear(self):
		return self._poll("clear")
	def load(self,user_data):
		return self._poll("load",user_data)
	def add(self,user_data):
		return self._poll("add",user_data)
	def playid(self,user_data):
		return self._poll("playid",user_data)
	def listallinfo(self):
		return self._poll("listallinfo")
	def play(self):
		return self._poll("play")
	def pause(self):
		return self._poll("pause")
	def stop(self):
		return self._poll("stop")
	def next(self):
		return self._poll("next")
	def previous(self):
		return self._poll("previous")
	def setvol(self,user_data):
		return self._poll("setvol",user_data)
	def repeat(self,user_data):
		return self._poll("repeat",user_data)
	def random(self,user_data):
		return self._poll("random",user_data)
	def shuffle(self,user_data=""):
		return self._poll("shuffle", user_data)
	def remove(self,user_data):
		return self._poll("remove", user_data)
	def save(self,user_data=""):
		return self._poll("save", user_data)
	

class fastMPC(object):
	timeout_id = None
	playlistinfo = []
	playlists = []
	db = []
	mpc_currentsong = {'artist': '', 'album': '', 'title': ''}
	mpc_status = {'state': 'stop'}
	mpc_stats = {}
	config = configparser.ConfigParser({'host': 'localhost',
					    'password': '',
					    'port': '6600',
					    'timeout': '10'})
	def __init__(self):
		# Load settings first
		configfile_path = os.path.join(self.createDataPath(), "config")
		if os.path.isfile(configfile_path):
			self.config.read(configfile_path)
		else:
			self.config.add_section('connection')
			self.config.add_section('collection')
		# Create MPD Client object
		self.mpc  = MPDPoller(self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port']))) # create client object
		self.mpc2 = MPDPoller(self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port']))) # This one is for updates only
		builder = Gtk.Builder()
		builder.add_from_file("%s.glade" % APPNAME.lower())
		builder.connect_signals({
			"on_mainwindow_destroy" : Gtk.main_quit,
			"on_menuitem_quit_activate" : Gtk.main_quit,
			"on_menuitem_connect_activate" : self.cb_connect,
			"on_menuitem_disconnect_activate" : self.cb_disconnect,
			"on_menuitem_updatedb_activate" : self.cb_updateDB,
			"on_menuitem_settings_activate" : self.cb_showSettings,
			"on_menuitem_about_activate" : self.cb_showAbout,
			"on_volumebutton_value_changed" : self.cb_changeVolume,
			"on_toolbutton_previous_clicked" : self.cb_previousSong,
			"on_toolbutton_next_clicked" : self.cb_nextSong,
			"on_toolbutton_playpause_clicked" : self.cb_playPausePlayback,
			"on_toolbutton_stop_clicked" : self.cb_stopPlayback,
			"on_playlist_view_drag_data_received" : self.cb_playlistDragDataReceived,
			"on_playlist_store_filter_rows_reordered" : self.cb_playlistRowsReordered,
			"on_playlist_view_row_activated" : self.cb_playlistDoubleClick,
			"on_playlists_view_row_activated" : self.cb_playlistsDoubleClick,
			"on_collection_view_row_activated" : self.cb_collectionDoubleClick,
			"on_folder_view_row_activated" : self.cb_folderDoubleClick,
			"on_playlist_filter_buffer_changed" : self.cb_playlistSearch,
			"on_collection_filter_button_clicked" : self.cb_collectionSearch,
			"on_toolbutton_playlist_loop_toggled" : self.cb_playlistLoopClick,
			"on_toolbutton_playlist_random_toggled" : self.cb_playlistRandomClick,
			"on_toolbutton_playlist_shuffle_clicked" : self.cb_playlistShuffleClick,
			"on_toolbutton_playlist_clear_clicked" : self.cb_playlistClearClick,
			"on_toolbutton_playlist_save_clicked" : self.cb_playlistSaveClick,
			"on_toolbutton_playlist_remove_clicked" : self.cb_playlistRemoveClick
			})
		self.gui_mainwindow = builder.get_object("mainwindow")
		self.gui_settingsdialog = builder.get_object("settings_dialog")
		self.gui_statusbar = builder.get_object("statusbar")
		self.gui_statusbar.push(self.gui_statusbar.get_context_id("connection"), "Keine Verbindung")
		self.gui_volumebutton = builder.get_object("volumebutton")
		self.gui_nowplaying_label = builder.get_object("nowplaying_label")
		self.gui_nowplaying_progressbar = builder.get_object("nowplaying_progressbar")
		self.gui_toolbutton_playpause = builder.get_object("toolbutton_playpause")
		self.gui_toolbutton_previous = builder.get_object("toolbutton_previous")
		self.gui_toolbutton_next = builder.get_object("toolbutton_next")
		self.gui_toolbutton_stop = builder.get_object("toolbutton_stop")
		self.gui_playlist_view = builder.get_object("playlist_view")
		self.gui_playlist_view.set_reorderable(True)
		self.gui_playlist_store = builder.get_object("playlist_store")
		self.gui_playlist_filter = builder.get_object("playlist_filter")
		self.gui_playlist_store_filter = builder.get_object("playlist_store_filter")
		self.gui_playlist_store_filter.set_visible_func(self.cb_playlistFilter)
		self.gui_playlists_store = builder.get_object("playlists_store")
		self.gui_collection_view = builder.get_object("collection_view")
		self.gui_collection_store = builder.get_object("collection_store")
		self.gui_collection_store_filter = builder.get_object("collection_store_filter")
		self.gui_collection_store_filter.set_visible_func(self.cb_collectionFilter)
		self.gui_collection_store_filter_sort = builder.get_object("collection_store_filter_sort")
		self.gui_collection_store_filter_sort.set_sort_column_id(3, Gtk.SortType.ASCENDING)
		self.gui_collection_filter = builder.get_object("collection_filter")
		self.gui_collection_filter_button = builder.get_object("collection_filter_button")
		self.gui_folder_view = builder.get_object("folder_view")
		self.gui_folder_store = builder.get_object("folder_store")
		self.gui_folder_store_sort = builder.get_object("folder_store_sort")
		self.gui_folder_store_sort.set_sort_column_id(0, Gtk.SortType.ASCENDING)
		self.gui_settings_connection_host = builder.get_object("settings_connection_host")
		self.gui_settings_connection_password = builder.get_object("settings_connection_password")
		self.gui_settings_connection_port = builder.get_object("settings_connection_port")
		self.gui_settings_connection_timeout = builder.get_object("settings_connection_timeout")
		self.gui_settings_artists_preferalbumartist = builder.get_object("settings_artists_preferalbumartist")
		self.gui_settings_artists_capitalize = builder.get_object("settings_artists_capitalize")
		self.gui_settings_artists_ignoreprefix = builder.get_object("settings_artists_ignoreprefix")
		self.gui_settings_compilations_use = builder.get_object("settings_compilations_use")
		self.gui_settings_compilations_artists = builder.get_object("settings_compilations_artists")
		self.gui_settings_compilations_folders = builder.get_object("settings_compilations_folders")
		self.gui_settings_albums_capitalize = builder.get_object("settings_albums_capitalize")
		self.gui_settings_songs_capitalize = builder.get_object("settings_songs_capitalize")


		self.gui_settings_connection_host.set_text(self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), -1)
		self.gui_settings_connection_password.set_text(self.config.get("connection","password",fallback=self.config['DEFAULT']['password']), -1)
		self.gui_settings_connection_port.set_value(int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port'])))
		self.gui_settings_connection_timeout.set_value(int(self.config.get("connection","timeout",fallback=self.config['DEFAULT']['timeout'])))
		self.gui_settings_artists_preferalbumartist.set_active(self.config.getboolean("collection","artists_preferalbumartist",fallback=False))
		self.gui_settings_artists_capitalize.set_active(self.config.getboolean("collection","artists_capitalize",fallback=True))
		self.gui_settings_artists_ignoreprefix.set_text(self.config.get("collection","artists_ignoreprefix",fallback="The,Die"), -1)
		self.gui_settings_compilations_use.set_active(self.config.getboolean("collection","compilations_use",fallback=True))
		self.gui_settings_compilations_artists.set_text(self.config.get("collection","compilations_artists",fallback="Various Artists,Various,VA,V.A.,V. A.,Verschiedene Interpreten"), -1)
		self.gui_settings_compilations_folders.set_text(self.config.get("collection","compilations_folders",fallback="Various Artists,Various,VA,V.A.,V. A.,Verschiedene Interpreten"), -1)
		self.gui_settings_albums_capitalize.set_active(self.config.getboolean("collection","albums_capitalize",fallback=True))
		self.gui_settings_songs_capitalize.set_active(self.config.getboolean("collection","songs_capitalize",fallback=False))

		self.gui_mainwindow.show_all()
		try:
			self.connect()
		except Exception as e:
			self._notify(APPNAME, "Konnte keine Verbindung zu %s:%i herstellen." % (self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port']))), "connection")

	# *****************************************************************************************
	# * Callback functions                                                                    *
	# *****************************************************************************************
	def cb_loadCollection(self):
		print("cb_loadCollection")
		print(self)
		self.cache_data = self.loadCollection()
		print("cb_loadCollectionFinished")

		self.mpc2.connect()
		self.mpc_stats = stats = self.mpc2.stats()
		self.updateStatus();
		self.timeout_id = GObject.timeout_add(500,self.cb_updateStatus, None)

		# Enable UI
		self.gui_playlist_view.set_sensitive(True)
		self.gui_volumebutton.set_sensitive(True)
		self.gui_nowplaying_label.set_sensitive(True)
		self.gui_nowplaying_progressbar.set_sensitive(True)
		self.gui_toolbutton_playpause.set_sensitive(True)
		self.gui_toolbutton_previous.set_sensitive(True)
		self.gui_toolbutton_next.set_sensitive(True)
		self.gui_toolbutton_stop.set_sensitive(True)

		threading.Thread(target=self.cb_parseCollection).start()
		return False

	def cb_parseCollection(self):
		if  self.cache_data:
			self.parseCache(self.cache_data,self.gui_collection_store,self.gui_folder_store)
		else:
			db = self.parseServer(self.db,self.gui_collection_store,self.gui_folder_store)
			if True:
				self.saveCache(self.mpc_stats,db)
		self._notify(APPNAME,"Sammlung geladen (%s Interpreten, %s Alben und %s Titel)" % (self.mpc_stats['artists'], self.mpc_stats['albums'], self.mpc_stats['songs']), "collection")
		return False

	def cb_connect(self, obj):
		self.connect()

	def cb_disconnect(self, obj):
		self.disconnect()

	def cb_updateStatus(self, data):
		return self.updateStatus()

	def cb_updateDB(self,obj):
		self.updateDB()

	def cb_showSettings(self,obj):
		self.showSettings()

	def cb_showAbout(self,obj):
		self.showAbout()

	def cb_changeVolume(self, obj, data):
		volume = int(round(data*100,0));
		self.changeVolume(volume)

	def cb_previousSong(self, obj):
		self.previousSong()

	def cb_nextSong(self, obj):
		self.nextSong()

	def cb_playPausePlayback(self, obj):
		self.playPausePlayback()

	def cb_stopPlayback(self, obj):
		self.stopPlayback()

	def cb_playlistDoubleClick(self, treeview, path, treeviewcolumn):
		treeiter = self.gui_playlist_store.get_iter(path)
		songid = self.gui_playlist_store.get_value(treeiter, 1)
		self.mpc.playid(songid)

	def cb_playlistSearch(self, entrybuffer, position, chars, n_chars=0):
		GObject.idle_add(self.cb_playlistSearchFilter)

	def cb_playlistSearchFilter(self):
		self.gui_playlist_store_filter.refilter()
		return False

	def cb_playlistFilter(self, model, treeiter, user_data):
		filterstring = self.gui_playlist_filter.get_text()
		if not filterstring:
			return True
		
		# Check Title
		if filterstring.lower() in str(model.get_value(treeiter, 2)).lower():
			return True

		# Check Artist
		if filterstring.lower() in str(model.get_value(treeiter, 3)).lower():
			return True

		# Check Album
		if filterstring.lower() in str(model.get_value(treeiter, 4)).lower():
			return True

		# Check Date
		if filterstring.lower() in str(model.get_value(treeiter, 7)).lower():
			return True

		# Check Genre
		if filterstring.lower() in str(model.get_value(treeiter, 8)).lower():
			return True

		return False

	def cb_collectionSearch(self, user_data=""):
		GObject.idle_add(self.cb_collectionSearchFilter)

	def cb_collectionSearchFilter(self):
		self.gui_collection_store_filter.refilter()
		return True

	def cb_collectionSearchFinished(self):
		return True

	def cb_collectionFilter(self, model, treeiter, user_data):
		filterstring = self.gui_collection_filter.get_text()
		# Check Title
		if not filterstring or (not model.iter_children(treeiter) and filterstring in str(model.get_value(treeiter, 0))):
			return True

		return False

	def cb_playlistsDoubleClick(self, treeview, path, treeviewcolumn):
		treeiter = self.gui_playlists_store.get_iter(path)
		playlistname = self.gui_playlists_store.get_value(treeiter, 0)
		self.replaceCurrentPlaylistWith(playlistname)

	def cb_collectionDoubleClick(self, treeview, path, treeviewcolumn):
		store = self.gui_collection_store_filter_sort
		treeiter = store.get_iter(path)
		GObject.idle_add(self._addNodeToPlaylist, (store, store.iter_children(treeiter), 1))
		#self._addNodeToPlaylist(store, store.iter_children(treeiter), 1)

	def cb_folderDoubleClick(self, treeview, path, treeviewcolumn):
		store = self.gui_folder_store_filter_sort
		treeiter = store.get_iter(path)
		GObject.idle_add(self._addNodeToPlaylist,(store, store.iter_children(treeiter), 1))

	def cb_playlistRandomClick(self, user_data):
		self.mpc.random(True)

	def cb_playlistShuffleClick(self, user_data):
		self.mpc.shuffle()

	def cb_playlistLoopClick(self, user_data):
		self.mpc.repeat(True)

	def cb_playlistClearClick(self, user_data):
		self.mpc.clear()

	def cb_playlistRemoveClick(self, user_data):
		pass

	def cb_playlistSaveClick(self, user_data):
		#self.mpc.save()
		pass

	def cb_playlistDragDataReceived(self, widget, drag_context, x, y, selection_data, info, timestamp):
		widget.stop_emission('drag_data_received')
		pass

	def cb_playlistRowsReordered(treemodel, path, treeiter, new_order, user_data):
		print("reordered!")


	def _iterNode(self, store, treeiter, result, column=-1):
		if not isinstance(result, list):
			result = []
		while treeiter != None:
			if column == -1:
				result.append(store[treeiter][:])
			else:
				try:
					row = store[treeiter][column]
				except Exception:
					pass
				else:
					if row:
						result.append(row)
			if store.iter_has_child(treeiter):
				childiter = store.iter_children(treeiter)
				self._iterNode(store, childiter, result, column)
			treeiter = store.iter_next(treeiter)
	def _addNodeToPlaylist(self, args):
		store, treeiter, column = args
		result = []
		
		self._iterNode(store, treeiter, result, column)
		for filename in result:
			if filename:
				self.mpc.add(filename)

	def _remove_keys(self, the_dict, rubbish):
		if isinstance(rubbish, tuple):
			for key in tuple(rubbish):
				if key in the_dict:
					del the_dict[key]
		else:
			if rubbish in the_dict:
				del the_dict[rubbish]
		for value in the_dict.items():
			# check for rubbish in sub dict
			if isinstance(value, dict):
				self._remove_keys(value, rubbish)
			elif isinstance(value, tuple):
				for item in value:
					if isinstance(item, dict):
						self._remove_keys(item, rubbish)

	# *****************************************************************************************
	# * Base functions                                                                        *
	# *****************************************************************************************
	def connect(self):
		self.mpc.connect()
		self._notify(APPNAME, "Verbunden mit %s:%i (MPD-Version %s), lade Sammlung..." % (self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port'])), self.mpc.mpd_version), "connection")
		GObject.idle_add(self.cb_loadCollection)
		#self.buildCollection()
		#self.cb_buildCollectionFinished()
		#self.mpc2.connect()
		#self._notify(APPNAME, "Verbunden mit %s:%i (MPD-Version %s)" % (host, port, self.mpc.mpd_version), "connection")
		#self.updateStatus();
		#self.timeout_id = GObject.timeout_add(500,self.cb_updateStatus, None)
		#self.buildCollection()

	def disconnect(self):
		GObject.source_remove(self.timeout_id)
		self.timeout_id = None

		# Disable UI
		self.gui_playlist_view.set_sensitive(False)
		self.gui_volumebutton.set_sensitive(False)
		self.gui_nowplaying_label.set_sensitive(False)
		self.gui_nowplaying_progressbar.set_sensitive(False)
		self.gui_toolbutton_playpause.set_sensitive(False)
		self.gui_toolbutton_previous.set_sensitive(False)
		self.gui_toolbutton_next.set_sensitive(False)
		self.gui_toolbutton_stop.set_sensitive(False)
		self.gui_collection_filter.set_sensitive(False)
		self.gui_collection_filter_button.set_sensitive(False)
		# Clear GtkTreeStores
		self.gui_collection_store.clear()
		self.gui_playlists_store.clear()
		self.gui_folder_store.clear()
		self.gui_playlist_store.clear()

		self.mpc.disconnect()                # disconnect from the server
		self._notify(APPNAME, "Keine Verbindung", "connection")

	def getDataPath(self):
		if sys.platform == "darwin":
			from AppKit import NSSearchPathForDirectoriesInDomains
			# http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
			# NSApplicationSupportDirectory = 14
			# NSUserDomainMask = 1
			# True for expanding the tilde into a fully qualified path
			datapath = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
		elif sys.platform == "win32":
			datapath = os.path.join(os.environ['APPDATA'], APPNAME)
		else:
			datapath = os.path.expanduser(os.path.join("~", "." + APPNAME.lower()))
		return datapath

	def showAbout(self):
		pixbuf = GdkPixbuf.Pixbuf.new_from_file("%s.png" % APPNAME.lower())
		dialog = Gtk.AboutDialog()
		dialog.set_name(APPNAME)
		dialog.set_version(str(APPVERSION));
		dialog.set_copyright("(c) 2012 Jan Holthuis")
		dialog.set_comments("FastMPC ist ein cachender MPD-Client in der Python-Programmiersprache.")
		dialog.set_website("http://homepage.ruhr-uni-bochum.de/Jan.Holthuis/fastmpd.html")
		dialog.set_logo(pixbuf);
		dialog.run();
		dialog.destroy()

	def createDataPath(self):
		datapath = self.getDataPath()
		if not os.path.exists(datapath):
			os.mkdir(datapath)
		return datapath

	def secondsToLength(self,seconds):
		return "%d:%02d" % (math.floor(int(seconds)/60),int(seconds)%60)

	def updateStatus(self):
		try:
			# Get server data
			mpc_status = self.mpc2.status()
			mpc_currentsong = self.mpc2.currentsong()
			playlists = self.mpc2.listplaylists()
			playlistinfo = self.mpc2.playlistinfo()
		except:
			self.disconnect();
			return False
		if mpc_status['state'] == "play":
			if (mpc_currentsong['artist'], mpc_currentsong['title'], mpc_currentsong['album']) != (self.mpc_currentsong['artist'], self.mpc_currentsong['title'], self.mpc_currentsong['album']) or mpc_status['state'] != self.mpc_status['state']:
				currentsong = "%s - %s (%s)" % (mpc_currentsong['artist'], mpc_currentsong['title'], mpc_currentsong['album'])
				# Update label
				self.gui_nowplaying_label.set_text(currentsong)
				self._notify(APPNAME, currentsong, "playback")
				del currentsong
			if 'song'  in self.mpc_status.keys() and mpc_status['song'] != self.mpc_status['song']:
				treeiter = self.gui_playlist_store.iter_nth_child(None, int(self.mpc_status['song']))
				self.gui_playlist_store.set_value(treeiter, 9, False)
				treeiter = self.gui_playlist_store.iter_nth_child(None, int(mpc_status['song']))
				self.gui_playlist_store.set_value(treeiter, 9, True)
				del treeiter
			self.mpc_currentsong = mpc_currentsong
			# Calculate time and progress
			currentsong_progress = mpc_status['time'].split(":");
			currentsong_progress_fraction = float(currentsong_progress[0])/float(currentsong_progress[1])
			currentsong_progress_f = [
				self.secondsToLength(currentsong_progress[0]),
				self.secondsToLength(currentsong_progress[1])
				]
			# Update progressbar
			self.gui_nowplaying_progressbar.set_fraction(currentsong_progress_fraction)
			self.gui_nowplaying_progressbar.set_text("%s / %s" % (currentsong_progress_f[0],currentsong_progress_f[1]))
			# Update Play/Pause button
			self.gui_toolbutton_playpause.set_stock_id(Gtk.STOCK_MEDIA_PAUSE)
		else:
			if mpc_status['state']=="stop":
				if mpc_status['state'] != self.mpc_status['state']:
					self.gui_nowplaying_label.set_text("Es wird nichts abgespielt.")
					self.gui_nowplaying_progressbar.set_fraction(0)
					self.gui_nowplaying_progressbar.set_text("0:00 / 0:00")
					self._notify(APPNAME, "Wiedergabe gestoppt.", "playback")
					if 'song'  in self.mpc_status.keys():
						treeiter = self.gui_playlist_store.iter_nth_child(None, int(self.mpc_status['song']))
						self.gui_playlist_store.set_value(treeiter, 9, False)
			# Update Play/Pause button
			self.gui_toolbutton_playpause.set_stock_id(Gtk.STOCK_MEDIA_PLAY)

		# Update volume
		self.gui_volumebutton.set_value(float(mpc_status['volume'])/100)
		self.mpc_status = mpc_status
		# Update Playlist
		if self.playlistinfo != playlistinfo:
			self.gui_playlist_store.clear()
			self.playlistinfo = playlistinfo
			for item in playlistinfo:
				if 'title' in item.keys():
					title = item['title']
				else:
					title = ""
				if 'artist' in item.keys():
					artist = item['artist']
				else:
					artist = ""
				if 'album' in item.keys():
					album = item['album']
				else:
					album = ""
				if 'time' in item.keys():
					time = self.secondsToLength(item['time'])
				else:
					time = "-:--"
				if 'track' in item.keys():
					track = int(item['track'].split("/")[0])
				else:
					track = None
				if 'date' in item.keys():
					date = item['date']
				else:
					date = None
				if 'genre' in item.keys():
					genre = str(item['genre'])
				else:
					genre = ""

				nowplaying = False
				if self.mpc_status['state'] != 'stop':
					if int(self.mpc_status['song']) == int(item['pos']):
						nowplaying = True
				self.gui_playlist_store.append([int(item['pos']), int(item['id']), title, artist, album, time, track, date, genre, nowplaying, 700])
		# Update Playlists list
		if self.playlists != playlists:
			self.playlists = playlists
			for item in playlists:
				self.gui_playlists_store.append([item['playlist'], item['last-modified']])
		return True

	def _notify(self, title, text, context=APPNAME.lower()):
		if context != "playback":
			self.gui_statusbar.pop(self.gui_statusbar.get_context_id(context))
			self.gui_statusbar.push(self.gui_statusbar.get_context_id(context), text)
		notification = Notify.Notification.new(title, text, 'dialog-information')
		notification.show()

	def updateDB(self):
		pass

	def showSettings(self):
		result = self.gui_settingsdialog.run()
		if result == Gtk.ResponseType.OK:
			# Connection Tab
			self.config.set("connection","host",self.gui_settings_connection_host.get_text())
			self.config.set("connection","password",self.gui_settings_connection_password.get_text())
			self.config.set("connection","port",str(int(self.gui_settings_connection_port.get_value())))
			self.config.set("connection","timeout",str(int(self.gui_settings_connection_timeout.get_value())))
			# Collection Tab
			self.config.set("collection","artists_preferalbumartist",'yes' if self.gui_settings_artists_preferalbumartist.get_active() else 'no')
			self.config.set("collection","artists_capitalize",'yes' if self.gui_settings_artists_capitalize.get_active() else 'no')
			self.config.set("collection","artists_ignoreprefix",self.gui_settings_artists_ignoreprefix.get_text())
			self.config.set("collection","compilations_use",'yes' if self.gui_settings_compilations_use.get_active() else 'no')
			self.config.set("collection","compilations_artists",self.gui_settings_compilations_artists.get_text())
			self.config.set("collection","compilations_folders",self.gui_settings_compilations_folders.get_text())
			self.config.set("collection","albums_capitalize",'yes' if self.gui_settings_albums_capitalize.get_active() else 'no')
			self.config.set("collection","songs_capitalize",'yes' if self.gui_settings_songs_capitalize.get_active() else 'no')
			# Save Config File
			configfile_path = os.path.join(self.createDataPath(), "config")
			with open(configfile_path, 'w') as configfile:
				self.config.write(configfile)
		self.gui_settingsdialog.hide()

	def changeVolume(self, volume):
		self.mpc.setvol(volume)

	def previousSong(self):
		self.mpc.previous()

	def nextSong(self):
		self.mpc.next()

	def playPausePlayback(self):
		if(self.mpc_status['state'] == "play"):
			self.mpc.pause()
		else:
			self.mpc.play()
		self.updateStatus()

	def stopPlayback(self):
		self.mpc.stop()

	def replaceCurrentPlaylistWith(self, playlistname):
		self.mpc.clear()
		self.mpc.load(playlistname)

	# *****************************************************************************************
	# * Load/Save collection and parse server/cache functions                                 *
	# *****************************************************************************************

	def loadCollection(self):
		print("loadCollection")
		try:
			stats = self.mpc.stats()
		except Exception:
			print("Unexpected error:", sys.exc_info()[0])

		cache_data = None
		print("stats",stats)
		print("cache_data",cache_data)
		try:
			cache_data = self.loadCache(stats)
		except IOError:
			print("Error: No local DB copy could be found or it is not accessible.")
			self.db = self.mpc.listallinfo()
		except ValueError:
			print("Error: DB mismatch. Your local copy is probably outdated. Downloading new DB from MPD-server.")
			self.db = self.mpc.listallinfo()
		except TypeError:
			print("Error: Your DB file is invalid or empty.")
			self.db = self.mpc.listallinfo()
		except Exception:
			print("Unexpected error:", sys.exc_info())
			self.db = self.mpc.listallinfo()

		return cache_data

	def loadCache(self, stats):
		print("cb_loadCache")
		db_file = os.path.join(self.createDataPath(), "dbcache_%s_%i_%s.dump" % (self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port'])), stats['db_update']))
		if not os.path.isfile(db_file):
			raise IOError
			return None
		f = open(db_file, "r")
		data = json.load(f)
		f.close()
		if 'uptime' in stats.keys():
			del stats['uptime']
		if 'uptime' in data[0].keys():
			del data[0]['uptime']
		if 'playtime' in stats.keys():
			del stats['playtime']
		if 'playtime' in data[0].keys():
			del data[0]['playtime']
		if stats != data[0]:
			raise ValueError
			return None
		if not (len(data[1]) == 2 and isinstance(data[1][0],dict) and isinstance(data[1][1],dict)):
			raise TypeError
			return None		
		return data[1]

	def saveCache(self, stats, db):
		# Uptime and playtime constantly change, so we delete these key from the dict
		if 'uptime' in stats.keys():
			del stats['uptime']
		if 'playtime' in stats.keys():
			del stats['playtime']
		# We include the stats for safety reasons (double checking), so that nobody ends up with an outdated db
		data = [stats, db]
		try:
			# Now let's open that file for writing...
			db_file = os.path.join(self.createDataPath(), "dbcache_%s_%i_%s.dump" % (self.config.get("connection","host",fallback=self.config['DEFAULT']['host']), int(self.config.get("connection","port",fallback=self.config['DEFAULT']['port'])), stats['db_update']))
			f = open(db_file, "w")
			# ...and dump the DB into that file
			json.dump(data,f)
			# We can now close that file
			f.close();
		except:
			print("Unexpected error:", sys.exc_info())

	def parseServer(self, db, collection_store, folder_store):
		collection = {}
		folders = {'_iter': None}
		config_compilations_artists = filter(bool,[x.strip() for x in self.config.get("collection","compilations_artists",fallback="Various Artists,Various,VA,V.A.,V. A.,Verschiedene Interpreten").split(",")])
		config_compilations_folders = filter(bool,[x.strip() for x in self.config.get("collection","compilations_folders",fallback="Various Artists,Various,VA,V.A.,V. A.,Verschiedene Interpreten").split(",")])
		config_artists_ignoreprefix = filter(bool,[x.strip() for x in self.config.get("collection","artists_ignoreprefix",fallback="The,Die").split(",")])
		config_artists_preferalbumartist = self.config.getboolean("collection","artists_preferalbumartist",fallback=False)
		config_compilations_use = self.config.getboolean("collection","compilations_use",fallback=True)
		config_compilations_artistname = self.config.get("collection","compilations_artistname","Verschiedene Interpreten")
		config_artists_capitalize = self.config.getboolean("collection","artists_capitalize",fallback=True)
		config_albums_capitalize = self.config.getboolean("collection","albums_capitalize",fallback=True)
		config_songs_capitalize = self.config.getboolean("collection","songs_capitalize",fallback=False)
		for item in db:
			for tag, value in item.items():
				if isinstance(value, list):
					item[tag] = ", ".join(set(value))

			if 'file' in item.keys():
				# Artists
				if 'artist' in item.keys():
					trackartist = artist = str(item['artist'])
				else:
					trackartist = artist = "Unbekannter Interpret"
				if config_artists_preferalbumartist:
					if 'albumartist' in item.keys():
						artist = str(item['albumartist'])

				if config_compilations_use:
					if compilations_artists:
						if artist in compilations_artists:
							artist = config_compilations_artistname
				
					if compilations_folders:
						if str(str(str(item['file']).split("/")[0]).split("\\")[0]).strip() in compilations_folders:
							artist = config_compilations_artistname

				artist = artist.strip()
				trackartist = trackartist.strip()

				if config_albums_capitalize:
					if artist == config_compilations_artistname:
						trackartist = ' '.join(word.capitalize() for word in trackartist.split())
					else:
						artist = ' '.join(word.capitalize() for word in artist.split())

				if config_artists_ignoreprefix:
					if artist != config_compilations_artistname:
						for ignore in config_artists_ignoreprefix:
							if artist.lower().startswith("%s " % ignore.lower()):
								artist = "%s, %s" % (artist[len(ignore):].strip(),ignore)

				if not artist in collection.keys():
					meta = [artist, "", Gtk.STOCK_ORIENTATION_PORTRAIT,artist]
					collection[artist] = {'_iter': collection_store.append(None, meta),
							      '_meta': meta}
				
				# Albums
				if 'album' in item.keys():
					album = str(item['album'])
				else:
					album = "Unbekanntes Album"

				if config_albums_capitalize:
					album = ' '.join(word.capitalize() for word in album.split())

				if not album in collection[artist].keys():
					meta = [album, "", Gtk.STOCK_CDROM, "%s - %s" % (artist, album)]
					collection[artist][album] = {'_iter': collection_store.append(collection[artist]['_iter'], meta),
								     '_meta': meta}
				# Discs
				if 'disc' in item.keys():
					try:
						disc = int(str(str(item['disc']).split("/")[0]).split("-")[0])
					except Exception:
						disc = 0
				else:
					disc = 0

				if not disc in collection[artist][album].keys():
					if disc:
						meta = ["CD %i" % disc, "", "", "%s - %s - %03d" % (artist, album, disc)]
						collection[artist][album][disc] = {'_iter': collection_store.append(collection[artist][album]['_iter'], meta),
										   '_meta': meta}
					else:
						collection[artist][album][disc] = {'_iter': collection[artist][album]['_iter']}
				# Songs
				song = None
				track = 0
				file = str(item['file'])
				if 'title' in item.keys():
					title = str(item['title'])
					if config_songs_capitalize:
						title = ' '.join(word.capitalize() for word in title.split())
				else:
					title = "Unbekannter Titel"
				if 'track' in item.keys():
					# Sometimes the track attribute contains something like "2/15" (Track 2 of 15).
					# We want only the first number, so we strip out the rest
					try:
						track = int(str(str(item['track']).split("/")[0]).split("-")[0])
					except Exception:
						track = 0
					else:
						if artist == config_compilations_artistname:
							song = "%i - %s - %s" % (track, trackartist, title)
						else:
							song = "%i - %s" % (track, title)
				if not song:
					if artist == config_compilations_artistname:
		 				song = "%s - %s" % (trackartist, title)
					else:
						song = title

				meta = [song, file, "", "%s - %s - %03d - %03d - %s" % (artist, album, disc, track, title)]
				collection_store.append(collection[artist][album][disc]['_iter'], meta)
				collection[artist][album][disc][song] = meta
				
				# Folderview stuff
				folder = os.path.basename(str(item['file']))
				currentpath = os.path.dirname(str(item['file'])).split(os.sep)
				folders_tmp = folders
				for item in currentpath:
					if item in folders_tmp.keys():
						folders_tmp = folders_tmp[item]
				meta = [folder, "", Gtk.STOCK_FILE]
				folder_iter = folder_store.append(folders_tmp['_iter'], meta)
				folders_tmp[folder] = {'_iter' : folder_iter, '_meta' : meta}

			# More Folderview stuff
			elif 'directory' in item.keys():
				folder = os.path.basename(str(item['directory']))
				currentpath = os.path.dirname(str(item['directory'])).split(os.sep)
				folders_tmp = folders
				for item in currentpath:
					if item in folders_tmp.keys():
						folders_tmp = folders_tmp[item]
				meta = [folder, "", Gtk.STOCK_DIRECTORY]
				folder_iter = folder_store.append(folders_tmp['_iter'], meta)
				folders_tmp[folder] = {'_iter' : folder_iter, '_meta' : meta}

		self.gui_folder_view.set_sensitive(True)
		self.gui_collection_view.set_sensitive(True)
		self.gui_collection_filter.set_sensitive(True)
		self.gui_collection_filter_button.set_sensitive(True)

		self._remove_keys(collection, ('_iter'))
		self._remove_keys(folders, ('_iter'))
		return (collection, folders)

	def parseCache(self, db, collection_store, folder_store):
		threading.Thread(target=self.parseCacheCollection, args=(db[0], collection_store)).start()
		threading.Thread(target=self.parseCacheFolders, args=(db[1], folder_store)).start()
	def parseCacheCollection(self, db, store):
		for artist_name, artist in db.items():
			artist_iter = store.append(None, artist['_meta'])
			for album_key, album in artist.items():
				if album_key != '_meta':
					album_iter = store.append(artist_iter, album['_meta'])
					for disc_key, disc in album.items():
						if disc_key != '_meta':
							if disc and '_meta' in disc.keys():
								disc_iter = store.append(album_iter, disc['_meta'])
							else:
								disc_iter = album_iter
							for song_key, song in disc.items():
								store.append(disc_iter, song)
		self.gui_collection_view.set_sensitive(True)
		self.gui_collection_filter.set_sensitive(True)
		self.gui_collection_filter_button.set_sensitive(True)
	def parseCacheFolders(self, folders, store):
		for folder in folders:
				self.parseCacheSubfolders(folders[folder], store)
		self.gui_folder_view.set_sensitive(True)
	def parseCacheSubfolders(self, folder, store, treeiter=None):
		if isinstance(folder, dict):
			treeiter_new = store.append(treeiter, folder['_meta'])
			for subfolder_key, subfolder in folder.items():
				if subfolder_key != '_meta':
					self.parseCacheSubfolders(subfolder, store, treeiter_new)
		else:
			store.append(treeiter, folder)


if __name__ == "__main__":
	app = fastMPC()
	Gdk.threads_init()
	Gtk.main()
