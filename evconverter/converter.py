# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pkg_resources
import config
import bookings

from gi.repository import Gtk


GDK_Escape = 0xff1b
version = pkg_resources.require("evconverter")[0].version
config = config.readConfig("./config.ini")


class MyApp(object):
    def focus_received(self, widget, data=None):
        self.focused = widget

    def file_convert(self, widget, data=None):
        bookings_file = self.filechooserbutton1.get_filename()
        debotrs_file = self.filechooserbutton2.get_filename()
        export_path = self.filechooserbutton2.get_filename()

        if bookings_file==None or debotrs_file==None or export_path==None:
            md = Gtk.MessageDialog(message_format="Wrong files or paths have been selected!")
            md.run()
            return
        else:
            filelist = [f for f in os.listdir(config["DIRS"]["outputdir"])]
            for f in filelist:
                os.remove(config["DIRS"]["outputdir"]+f)
            bookings.makeXMLAccounts(debotrs_file, config["DIRS"]["outputdir"], config)
            newbookingid = bookings.makeXMLTransactions(bookings_file, config["DIRS"]["outputdir"],
             config)

        pass

    def file_new(self, widget, data=None):
        self.filechooserbutton1.unselect_all()
        self.filechooserbutton2.unselect_all()
        pass

    def file_options(self, widget, data=None):
        buffer = Gtk.TextBuffer.new()
        cfgfile = open("./config.ini", "r")
        data = cfgfile.read()
        cfgfile.close()
        buffer.set_text(data)
        self.options_text.set_buffer(buffer)
        result = self.options.run()
        if result == 1:
            buffer = self.options_text.get_buffer()
            cfgfile = open("./config.ini", "w")
            data = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            cfgfile.write(data)
            cfgfile.close()
        self.options.hide()

    def link_click(self, widget, data=None):
        os.system("htmlview "+widget.get_uri())

    def gtk_main_quit(self, widget, data=None):
        Gtk.main_quit()

    def on_window1_remove(self, widget, data=None):
        Gtk.main_quit()

    def key_pressed(self, widget, event, data=None):
        if (event.keyval == GDK_Escape):
            Gtk.main_quit()

    def help_about(self, widget, data=None):
        self.about.run()
        self.about.hide()

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("converter.xml")

        self.window = builder.get_object("window1")

        self.filechooserbutton1 = builder.get_object("filechooserbutton1")
        self.filechooserbutton2 = builder.get_object("filechooserbutton2")
        self.filechooserbutton3 = builder.get_object("filechooserbutton3")

        self.about = builder.get_object("aboutdialog1")
        self.about.set_version(version)

        self.options = builder.get_object("dialog1")
        self.options_text = builder.get_object("textview1")

        self.statusbar = builder.get_object("statusbar1")

        builder.connect_signals(self)


if __name__ == "__main__":
    App = MyApp()
    App.filechooserbutton3.set_current_folder(config["DIRS"]["outputdir"])
    App.window.show()
    Gtk.main()
