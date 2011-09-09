import commands
import urllib
import gettext
import gconf
import gobject
import subprocess
import os
import ConfigParser
import tempfile
from gi.repository import Nautilus, Gtk

FIREFOX  = 'firefox-firma'
PK12UTIL_CMD = '/usr/bin/pk12util'
SUPPORTED_FORMATS = 'application/x-pkcs12'
gettext.install("nautilus-cert-handler")

class CertHandler(gobject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass
    
    def menu_activate_cb(self, menu, file):
        if file.is_gone():
            return
        
        # Strip leading file://
        if self.is_firefox_running():
            msg = _('It was not possible install any certificate because firefox is running. Please close Firefox and retry')
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE, msg)
            dialog.set_title(_('Error'))
            dialog.set_position(Gtk.WindowPosition.CENTER)
            dialog.run()
            dialog.destroy()
            return False

        filename = urllib.unquote(file.get_uri()[7:])
        attempts = 0
        valid = False
        print_warning = False
        while attempts < 3 and not valid:
            password = self._ask_for_password(file.get_name(), print_warning)
            if password:
                valid = self.add_user_certificate(filename, password)
                attempts += 1
                print_warning = True
            else:
                return False # User cancel
        if not valid:
            msg = _('It was not possible to add the certificate %s because the password is not valid') % file.get_name()
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE, msg)
            dialog.set_title(_('Error configuring %s') % file.get_name())
            dialog.set_position(Gtk.WindowPosition.CENTER)
            dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                                       Gtk.ButtonsType.CLOSE, _("The certificate %s has been installed") % file.get_name())
            dialog.set_title(_('Certificate %s installed') % file.get_name())
            dialog.set_position(Gtk.WindowPosition.CENTER)
            dialog.run()
            dialog.destroy()

        
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

    def _ask_for_password(self, certificate, warn_user=False):
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK_CANCEL)
        dialog.set_title(_('Configuring %s') % certificate)
        dialog.set_position(Gtk.WindowPosition.CENTER)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_markup(_('Insert your password to unlock the certificate from file <b>%s</b>') % certificate)
        if warn_user:
            dialog.format_secondary_text(_('The password is not valid'))
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        entry.set_visibility(False) # this entry is for passwords
        entry.show()
        parent = dialog.get_content_area().get_children()[0].get_children()[1]
        parent.pack_start(entry, False, False, False)
        result = dialog.run()
        retval = None
        if result == Gtk.ResponseType.OK:
            retval = entry.get_text()
        dialog.destroy()
        return retval

    def add_user_certificate(self, certificate_file, password):
        profile = self.get_default_profile_dir()
        if not profile:
            return False

        fd, password_file = tempfile.mkstemp(text=True)
        os.write(fd, password)
        os.close(fd)

        cmd = '%s -i "%s" -d "%s" -w "%s"'
        cmd = cmd % (PK12UTIL_CMD, certificate_file, profile, password_file)
        status, output = commands.getstatusoutput(cmd)
        os.unlink(password_file)
        return status == 0

    def is_firefox_running(self):
        cmd = 'ps -A'
        status = False
        output = commands.getoutput(cmd)
        if FIREFOX in output:
            status = True
        return status

    def get_default_profile_dir(self):
        user_dir = os.path.expanduser('~')
        ff_dir = os.path.join(user_dir, '.mozilla', 'firefox')
        if not os.path.exists(ff_dir):
            return

        config = ConfigParser.ConfigParser()
        config.readfp(file(os.path.join(ff_dir, 'profiles.ini')))
        profiles = [section for section in config.sections() \
                    if config.has_option(section, 'Name')]

        if len(profiles) == 1:
            default = profiles[0]
        else:
            for profile in profiles:
                if (config.has_option(profile, 'Name') and
                    config.get(profile, 'Name') == 'firefox-firma'):
                    default = profile

        path = config.get(default, 'Path')
        return os.path.join(ff_dir, path)
