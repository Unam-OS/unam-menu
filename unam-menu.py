#!/usr/bin/python3

import gi
import os
import re
import threading
import subprocess

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

def log(message):
    file = "/home/elbullazul/.config/unam/unam-menu/logs/log"

    with open(file, "a") as logfile:
        logfile.write(message)

class unam_menu(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Unam Menu")

        self.semaphore = threading.Semaphore(4)
        self.wrapper = Gtk.VBox()
        self.scrollbox = Gtk.ScrolledWindow()
        self.scrollframe = Gtk.Viewport()
        self.box = Gtk.Box(spacing=6)   
        self.spacer = Gtk.Box()
        self.controlbox = Gtk.HBox(spacing=2)

        self.btn_quit = Gtk.Button()
        self.icon = Gtk.Image()
        self.icon.set_from_icon_name('gtk-close', Gtk.IconSize.DIALOG)
        self.btn_quit.add(self.icon)

        classes = self.btn_quit.get_style_context()
        classes.add_class('flat')

        self.app_grid = Gtk.Grid()

        self.add(self.wrapper)
        self.controlbox.pack_start(self.spacer, True, True, 0)
        self.controlbox.pack_start(self.btn_quit, False, False, 0)
        self.wrapper.pack_start(self.controlbox, False, False, 0)
        self.wrapper.pack_start(self.scrollbox, True, True, 0)
        self.scrollbox.add(self.scrollframe)
        self.scrollframe.add(self.box)

        self.box.add(self.app_grid)

        self.btn_quit.connect('clicked', Gtk.main_quit)
        self.btn_list = []

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

                icon = "void"
                name = "void"
                desc = "void"
                cmd = "void"

                for line in buffer:
                    if line.startswith("Icon="):
                        icon = line
                        icon = icon[5:]
                        icon = icon.rstrip()
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

                    if icon is not "void" and name is not "void" and cmd is not "void" and desc is not "void":

                        self.image = Gtk.Image()
                        self.image.set_from_icon_name(icon, Gtk.IconSize.DIALOG)

                        self.btn_list.append(Gtk.Button())

                        self.label = Gtk.Label(name, 12)
                        self.layoutbox = Gtk.VBox()
                        self.layoutbox.add(self.image)
                        self.layoutbox.add(self.label)

                        classes = self.btn_list[app_id].get_style_context()
                        classes.add_class('flat')

                        self.btn_list[app_id].add(self.layoutbox)
                        self.btn_list[app_id].set_hexpand(True)
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
        with self.semaphore:
                os.system(path + command)
                log("App launched: " + command)

    def build_menu(self):

        column = 1
        row = 1
        items = len(self.btn_list)
        for item in range(0, items):
                self.app_grid.attach(self.btn_list[item], column, row, 1, 1)
                if column == 3:
                        column = 0
                        row += 1
                column += 1
        log('Added items to menu')

menu = unam_menu()
menu.set_decorated(False)

menu.set_skip_taskbar_hint(True)
menu.set_skip_pager_hint(True)

menu.resize(660,600)
menu.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

menu.connect("delete-event", Gtk.main_quit)
menu.show_all()
Gtk.main()
