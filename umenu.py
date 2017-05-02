#!/usr/bin/python3

import gi
import os
import re
import sys
import threading
import subprocess
import setproctitle

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

setproctitle.setproctitle('unam-menu')

def log(message):
    file = "/home/elbullazul/.config/unam/unam-menu/logs/log"

    with open(file, "a") as logfile:
        logfile.write(message)

def getScreenSize():
    output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',shell=True,stdout=subprocess.PIPE).communicate()[0]
    output = output.rstrip()
    output = str(output)
    
    # remove unnecessary characters
    output = output[2:]
    output = output[:-1]
    return output

class unam_menu(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Unam Menu")

        self.semaphore = threading.Semaphore(4)
        self.wrapper = Gtk.HBox()
        self.scrollbox = Gtk.ScrolledWindow()
        self.scrollframe = Gtk.Viewport()
        self.box = Gtk.Box(spacing=6)   
        self.spacer = Gtk.Box()
        self.search_entry = Gtk.Entry()

        self.btn_quit = Gtk.Button()
        self.icon = Gtk.Image()
        self.icon.set_from_icon_name('gtk-close', Gtk.IconSize.DIALOG)

        self.app_line = Gtk.HBox()

        self.add(self.wrapper)
        self.wrapper.pack_start(self.search_entry, False, False, 0)
        self.wrapper.pack_start(self.scrollbox, True, True, 0)
        self.scrollbox.add(self.scrollframe)
        self.scrollframe.add(self.box)
        self.box.add(self.app_line)

        self.search_entry.set_icon_from_icon_name(1, 'stock-search')
        self.search_entry.set_icon_tooltip_text(1, 'Search for Applications')
        self.search_entry.connect('changed', self.search)
        self.btn_list = []
        self.labels = []

        self.add_items()
        self.build_menu()

    def add_items(self):

        path = '/usr/share/applications'
        app_id = 0

        for file in os.listdir(path):
            # print(file)

            if os.path.isfile(os.path.join(path, file)):

                buffer = open(path + '/' + file, "r")
                # print(buffer.read())

                name = "void"
                desc = "void"
                cmd = "void"

                for line in buffer:
                    if line.startswith("Name="):
                        name = line
                        name = name[5:]
                        name = name.rstrip()
                    if line.startswith("Comment="):
                        desc = line
                        desc = desc[8:]
                        desc = desc.rstrip()
                    if line.startswith("Exec="):
                        cmd = line
                        cmd = cmd[5:]
                        cmd = cmd.rstrip()

                    if name is not "void" and cmd is not "void" and desc is not "void":


                        self.btn_list.append(Gtk.Button())

                        self.labels.append(Gtk.Label(name, 12))

                        classes = self.btn_list[app_id].get_style_context()
                        classes.add_class('flat')

                        self.btn_list[app_id].add(self.labels[app_id])
                        self.btn_list[app_id].set_tooltip_text(desc)
                        self.btn_list[app_id].connect("clicked" , self.button_click, cmd)

                        app_id += 1

                        icon = "void"
                        name = "void"
                        desc = "void"
                        cmd = "void"

        log("Apps loaded")

    def button_click(self, button, *data):
        path = "/usr/bin/"
        command = str(data)
        command = command[2:]
        command = command[:-3]

        # Start process with new thread
        # subprocess.Popen(command ,shell=True, stdout=subprocess.PIPE).communicate()[0]

        with self.semaphore:
                os.system(path + command)
                log("App launched: " + command)

    def clear(self):
        items = len(self.btn_list)
        for item in range(0, items):
                self.app_line.remove(self.btn_list[item])

    def sort(self):
        items = len(self.btn_list)
        
        for item in range(0, items):
            if self.search_entry.get_text().lower() in self.labels[item].get_text().lower():
                self.app_line.add(self.btn_list[item])

    def search(self, entry):
        self.clear()
        
        self.sort()

    def build_menu(self):

        items = len(self.btn_list)
        for item in range(0, items):
                self.app_line.add(self.btn_list[item])

        log('Added items to menu')

log('Started in umenu mode')

menu = unam_menu()
menu.set_decorated(False)

# menu.set_skip_taskbar_hint(True)
# menu.set_skip_pager_hint(True)

resolution = getScreenSize()
resolution = resolution.split('x')

menu.resize(int(resolution[0]),20)
# menu.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

menu.connect("delete-event", Gtk.main_quit)

menu.show_all()
Gtk.main()
