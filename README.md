fastMPC
=======

fastMPC is a client for the [Music Player Daemon (MPD)](http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki).
It's written in [Python 3](http://python.org/download/releases/3.0/) and uses [GTK+ 3](http://developer.gnome.org/gtk3/stable/gtk.html) and [python-mpd2](https://github.com/Mic92/python-mpd2).

What is special about fastMPC?
-----------------------------

fastMPC was written, because most other clients rely on search functions
provided by the MPD server. Usually, this would be fine, but it's awfully
slow if your MPD server runs on an old machine (e.g. [NSLU2](http://en.wikipedia.org/wiki/NSLU2)
with 266 MHz and 32 MB RAM) and has a big collection. fastMPC searches
locally. Additionally, it caches the music collection. As long as the
collection is not rescanned, it uses the cached version instead of 
downloading the whole collection every time it starts.

Getting the latest source code
------------------------------

If you would instead like to use the latest source code, you can grab a copy
of the development version from git by running the command:

    $ git clone git://github.com/Holzhaus/fastMPC.git
