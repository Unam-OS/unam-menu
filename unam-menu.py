#!/usr/bin/python3

import gi
import os
import re
import sys
import threading
import subprocess
import setproctitle

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, Gdk, Pango, Gio, GLib, Keybinder

setproctitle.setproctitle('unam-menu')

# Files
home = os.getenv("HOME") + '/'
applications = '/usr/share/applications/'
log_file = home + '.config/unam/unam-menu/log'

def check_files():
    global_conf = home + '.config/unam'
    local_conf = home + '.config/unam/unam-menu'

    if not os.path.isdir(global_conf):
        print('Creating config folder')
        os.makedirs(global_conf)
        
    if not os.path.isdir(local_conf):
        print('Setting up config')
        os.makedirs(local_conf)

check_files()

gapps = Gio.File.new_for_path(applications)
dir_changed = gapps.monitor_directory(Gio.FileMonitorFlags.NONE, None)

def get_screen_size(x, y):
    display = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',shell=True,stdout=subprocess.PIPE).communicate()[0]
    display = str(display.rstrip())[2:-1]
    display = display.split('x')
    
    if x == True and y == True:
        return display
    elif x == True and y == False:
        return display[0]
    elif x == False and y == True:
        return display[1]
    elif x == False and y == False:
        return display[0] + 'x' + display[1]

def log(message):
    with open(log_file, "a+") as logfile:
        logfile.write(message + '\n')

class spacer():
    def __init__(self):
        self.box = Gtk.Box()
        self.label = Gtk.Label('')
        self.box.add(self.label)
        #self.box.set_sensitive(False)
        
    def get_box(self):
        return self.box
        
class appbutton():
    def __init__(self):
        self.button = Gtk.Button()
        self.label = Gtk.Label()
        self.icon = Gtk.Image()
        self.layoutbox = Gtk.VBox()
        self.command = ''
        
        self.build()
        
    def build(self):
        self.flat()
        self.label.set_alignment(0.5,0.5)
        self.button.set_hexpand(True)
        self.layoutbox.add(self.icon)
        self.layoutbox.add(self.label)
        self.button.add(self.layoutbox)
        
    def construct(self, icon_name, label_text, tooltip_text, command):
        self.set_icon(icon_name, Gtk.IconSize.DIALOG)
        self.set_label(label_text)
        self.set_tooltip(tooltip_text)
        self.set_command(command)
        
    def flat(self):
        classes = self.button.get_style_context()
        classes.add_class('flat')
        
    def on_click(self, button, cmd):
        os.system(cmd + ' &')
        log('App launched: ' + cmd)
        menu.invisible(None, None)
        
    def set_icon(self, icon_name, icon_size):
        self.icon.set_from_icon_name(icon_name, icon_size)
        
    def get_icon(self):
        return self.icon.get_from_icon_name()
        
    def set_label(self, text):
        self.label.set_text(text)
        
    def get_label(self):
        return self.label.get_text()
        
    def set_tooltip(self, text):
        self.button.set_tooltip_text(text)
        
    def get_tooltip(self):
        return self.button.get_tooltip_text()
        
    def set_command(self, cmd):
        self.command = cmd
        self.button.connect('clicked', self.on_click, cmd)
        
    def get_command(self):
        return self.command
        
    def get_button(self):
        return self.button
        
    def get_info(self):
        return self.get_label(), self.get_command(), self.get_tooltip() #, self.get_icon()

class unam_menu(Gtk.Window):

    _current_accel_name = None

    def __init__(self):
        log('Initialized new instance')
        Gtk.Window.__init__(self, title="Unam Menu")
        
        self.icon = Gtk.Image()
        self.icon.set_from_icon_name('app-launcher', Gtk.IconSize.MENU)
        
        self.drawer_mode = False
        self.visible = False
        self.no_search = True
        self.update = dir_changed

        # keyboard shortcuts
        accel = Gtk.AccelGroup()
        accel.connect(Gdk.keyval_from_name('Q'), Gdk.ModifierType.CONTROL_MASK, 0, Gtk.main_quit)
        self.add_accel_group(accel)
        self.bind_hotkey()

        self.connect("delete-event", Gtk.main_quit)
        self.connect('focus-in-event', self.on_focus_in)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key_press_event', self.on_key_press)
        self.update.connect('changed', self.update_list)

        self.semaphore = threading.Semaphore(4)
        self.wrapper = Gtk.VBox()
        self.scrollbox = Gtk.ScrolledWindow()
        self.scrollframe = Gtk.Viewport()
        self.box = Gtk.Box(spacing=6)   
        self.spacer_left = Gtk.Box()
        self.spacer_right = Gtk.Box()
        self.controlbox = Gtk.HBox(spacing=2)
        self.searchbox = Gtk.Box(spacing=20)
        self.app_grid = Gtk.Grid()
        self.search_entry = Gtk.Entry()
        
        self.add(self.wrapper)
        self.controlbox.pack_start(self.spacer_left, True, True, 0)
        self.controlbox.pack_start(self.search_entry, True, True, 0)
        self.controlbox.pack_start(self.spacer_right, True, True, 0)
        self.wrapper.pack_start(self.controlbox, False, False, 0)
        self.wrapper.pack_start(self.scrollbox, True, True, 0)
        self.scrollbox.add(self.scrollframe)
        self.scrollframe.add(self.box)
        self.box.add(self.app_grid)

        self.spacer_right.set_halign(Gtk.Align.END)
        self.search_entry.set_icon_from_icon_name(1, 'search')
        self.search_entry.set_icon_tooltip_text(1, 'Search for Applications')
        self.search_entry.connect('changed', self.search)
        self.search_entry.connect('activate', self.launch)

        self.app_list = []
        
        # Drawer mode
        if len(sys.argv) > 1:
            if sys.argv[1] == '-d' or '--drawer':
                print('Set to drawer mode')
                log('Initialized in drawer mode. Configuring...')
                self.drawer_mode = True
                self.conf_drawer()

        self.load_apps()
        self.assemble()
        self.configure()
        
        self.show_all()
        self.set_focus()
        
    def conf_drawer(self):
        self.btn_quit = Gtk.Button()
        self.btn_quit.icon = Gtk.Image()

        self.btn_quit.add(self.btn_quit.icon)
        self.spacer_right.add(self.btn_quit)
        self.btn_quit.icon.set_from_icon_name('gtk-close', Gtk.IconSize.MENU)

        classes = self.btn_quit.get_style_context()
        classes.add_class('flat')
        
    def bind_hotkey(self): # thanks ulauncher
        Keybinder.init()
        accel_name = "<Super>Q" # <Primary> <Control> <Alt> <Shift>
        
        # bind in the main thread
        GLib.idle_add(self.set_hotkey, accel_name)

    def unbind(self, accel_name):
        Keybinder.unbind(accel_name)

    def set_hotkey(self, accel_name):
        if self._current_accel_name:
            Keybinder.unbind(self._current_accel_name)
            self._current_accel_name = None
        
        Keybinder.bind(accel_name, self.on_hotkey_press)
        self._current_accel_name = accel_name
        #self.notify_hotkey_change(accel_name)
        
    def update_list(self, m, f, o, event):
        if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            print('Updating app list')
            self.app_list = []

            self.load_apps()
            self.clear()
            self.assemble()
            #self.show_all()
            
    def load_apps(self):
        app_count = 0
        
        apps = os.listdir(applications)
        apps = sorted(apps)

        #for file in os.listdir(applications):
        for app in apps:
            if os.path.isfile(os.path.join(applications, app)):
                buffer = open(applications + '/' + app, "r")

                name = "void"
                icon = "void"
                desc = "void"
                cmd = "void"

                for line in buffer:
                    if line.startswith("Icon="):
                        icon = line[5:].rstrip()
                    if line.startswith("Name="):
                        name = line[5:].rstrip()
                    if line.startswith("Comment="):
                        desc = line[8:].rstrip()
                    if line.startswith("Exec="):
                        cmd = line[5:].rstrip().lower()
                        cmd = cmd.replace("%u","")
                        cmd = cmd.replace("%f","")

                    if icon is not "void" and name is not "void" and cmd is not "void" and desc is not "void":
                        btn_app = appbutton()
                        btn_app.construct(icon, name, desc, cmd)

                        self.app_list.append(btn_app)
                        app_count += 1

                        icon = "void"
                        name = "void"
                        desc = "void"
                        cmd = "void"
                        
    def assemble(self):
        column = 1
        row = 1
        print(len(self.app_list))
        for item in range(0, len(self.app_list)):
            self.app_grid.attach(self.app_list[item].get_button(), column, row, 1, 1)
            if column == 3:
                column = 0
                row += 1
            column += 1

    def on_hotkey_press(self, event):
        if self.visible:
            self.invisible(None, None)
        else:
            self.set_visible(None, None)
        
    def set_focus(self):
        self.present()
        self.set_modal(True)
        self.set_keep_above(True)
            
    def set_visible(self, object, event):
        self.show_all()
        self.set_focus()
        self.search_entry.grab_focus()
        self.visible = True
        print('toggle visible')

    def invisible(self, object, event):
        self.hide()
        self.search_entry.set_text('')
        self.no_search = True
        self.visible = False
        print('toggle invisible')
        
    def configure(self):
        self.set_decorated(False)
        self.resize(660,600)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        #self.set_size_request(350,5)
        
        if self.drawer_mode:
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            self.set_gravity(Gdk.Gravity.CENTER)
        else:
            self.move(0, int(get_screen_size(False, True)))
        
    def on_key_press(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        if 'Escape' in key:
            print(str(key))
            self.invisible(None, None)

    def on_focus_in(self, widget, event):
        self.visible = True

    def on_focus_out(self, widget, event):
        t = threading.Timer(0.07, lambda: not self.visible or self.invisible(None, None))
        t.start()

    def search(self, entry):
        if self.search_entry.get_text() != '':
            if self.no_search == True:
                self.no_search = False
            self.found = False
            self.clear()
            self.populate()
            self.show_all()
        else:
            self.clear()
            self.assemble()
            self.show_all()
        
    def clear(self):
        for widget in self.app_grid:
            self.app_grid.remove(widget)

    def populate(self):
        apps = 0
        row = 1
        column = 1
        query = self.search_entry.get_text()
        if query != "":
            for item in range(0, len(self.app_list)):
                if query in str(self.app_list[item].get_info()):
                    self.app_grid.attach(self.app_list[item].get_button(), column, row, 1,1)
                    apps += 1
                    self.found = True
                    if column == 3:
                        row += 1
                        column = 0
                    column += 1
                    
        if apps == 0:
            label = Gtk.Label('No items found')
            label.set_hexpand(True)
            label.set_alignment(0.5,0)
            self.found = False
            self.app_grid.attach(label, 0, 0, 1,1)

    def launch(self, *data):
        if (self.found):
            child = self.app_grid.get_children()
            print(len(child))
            child[len(child) - 1].grab_focus()
            self.activate_focus()
        else:
            self.invisible(None, None)
            
menu = unam_menu()
menu.invisible(None, None)
Gtk.main()
