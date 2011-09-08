import urllib
import gettext
import gconf
import gobject
import subprocess
from gi.repository import Nautilus, Gtk

SUPPORTED_FORMATS = 'application/x-pkcs12'
gettext.install("nautilus-cert-handler")

class CertHandler(gobject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass
    
    def menu_activate_cb(self, menu, file):
        if file.is_gone():
            return
        
        # Strip leading file://
        filename = urllib.unquote(file.get_uri()[7:])
        self.gconf.set_string(BACKGROUND_KEY, filename)
        self.Res = subprocess.Popen(['certutil', '-A', '-n', file.get_name(), '-t', '"p,p,p"', '-i', filename, '-d', '/usr/share/firefox-firma/profiles/firefox/firefox-firma/'], stdout=subprocess.PIPE)
        Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE, "Hello World").run()

        
    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        file = files[0]

        # We're only going to put ourselves on images context menus
        if not file.get_mime_type() in SUPPORTED_FORMATS:
            return

        # Gnome can only handle file:
        # In the future we might want to copy the file locally
        if file.get_uri_scheme() != 'file':
            return

        item = Nautilus.MenuItem(name='Nautilus::cert_handler',
                                 label=_('Install certificate'),
                                 tip=_('Install selected certificate file to your Mozilla Firefox'),
                                 icon='nautilus-cert-handler')
        item.connect('activate', self.menu_activate_cb, file)
        return item,
