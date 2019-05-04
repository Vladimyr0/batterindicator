#!/usr/bin/env python3
#
# options: 
#           -k/m - keyboard/mouse (required)
#           -d/w - dark/white theme (default is dark)
#           -p - show percentage in the label
#           --l=N - override warning limit to N% (0 to off)
#
import os
import signal
import subprocess
import sys
import getopt
import time
from threading import Thread
try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('AppIndicator3', '0.1')
    gi.require_version('Notify', '0.7')
    from gi.repository import Gtk, AppIndicator3, GObject, GdkPixbuf, Notify
except ImportError as exc:
    raise ImportError(
        "Install the library 'python3-gi' \n{0}".format(str(exc))
    )
icon_folder = 'icons'
selected_device = ''
device_icon = ''
show_percentage = False
selected_theme = 'd'
warning_limit = 10
usage = 'usage: "batterindicator.py -k/m [-d/w] [-p] [--l=N]"'

class Indicator():
    def __init__(self):
        global selected_device, device_icon, show_percentage, selected_theme, warning_limit
        try:
            opts, args = getopt.getopt(sys.argv[1:],"kmdwp",["l="])
        except getopt.GetoptError:
            print (usage)
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-k':
                selected_device = 'keyboard'
                device_icon = 'kbd'
            elif opt == '-m':
                selected_device = 'mouse'
                device_icon = 'mse'
            elif opt == '-w':
                selected_theme = 'w'
            elif opt == '-p':
                show_percentage = True
            elif opt == '--l':
                try:
                    warning_limit = int(arg)
                    print ('warning_limit = '+str(warning_limit))
                except ValueError:
                    warning_limit = 10
        if selected_device == '':
            print (usage)
            sys.exit(2)

        self.app = 'batterindicator'
        self.indicator = AppIndicator3.Indicator.new(
            self.app, 
            os.path.abspath(icon_folder+"/bat_"+device_icon+"_"+selected_theme+"_nn.png"),
            AppIndicator3.IndicatorCategory.HARDWARE)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)       
        self.indicator.set_menu(self.create_menu())
        if show_percentage:
            self.indicator.set_label("??%", self.app)
        Notify.init(self.app)
        self.update = Thread(target=self.show_perc)
        self.update.setDaemon(True)
        self.update.start()

    def create_menu(self):
        menu = Gtk.Menu()
        item_about = Gtk.MenuItem('about')
        item_about.connect('activate', self.about)
        menu.append(item_about)
        menu_sep = Gtk.SeparatorMenuItem()
        menu.append(menu_sep)
        item_info = Gtk.MenuItem('info')
        item_info.connect('activate', self.message)
        menu.append(item_info)
        menu_sep = Gtk.SeparatorMenuItem()
        menu.append(menu_sep)
        item_quit = Gtk.MenuItem('quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)
        menu.show_all()
        return menu

    def show_perc(self):
        lp = 100
        time.sleep(3)
        while True:
            args = ['/bin/sh','-c','upower -i $(upower -e | grep '+selected_device+') | grep percentage: | grep -o -E "[0-9]+"']
            s = subprocess.check_output(args).decode('Utf-8').rstrip()
            try:
                p = int(s)
            except ValueError:
                p = -1
            iname = {
                80 < p <= 100: "100",
                60 < p <= 80: "80",
                40 < p <= 60: "60",
                20 < p <= 40: "40",
                0 <= p <= 20: "20",
                p < 0: "nn"
            }[True]            
            if show_percentage:
                plabel = s+"%"
                GObject.idle_add(self.indicator.set_label, plabel, self.app,  priority=GObject.PRIORITY_DEFAULT)
            GObject.idle_add(self.indicator.set_icon, 
                os.path.abspath(icon_folder+"/bat_"+device_icon+"_"+selected_theme+"_"+iname+".png"),
            priority=GObject.PRIORITY_DEFAULT)
            if (0 <= p < 10) and (lp >= 10): 
                Notify.Notification.new("<b>Performance MX</b>", 
                    "\u0411\u0430\u0442\u0430\u0440\u0435\u044F \u0440\u0430\u0437\u0440\u044F\u0436\u0435\u043D\u0430!", 
                os.path.abspath(icon_folder+"/battery-charge-20.png")).show()    
            lp = p
            time.sleep(30)

    def stop(self, source):
        Gtk.main_quit()

    def about(self, source):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(
            os.path.abspath(icon_folder+"/battery-charge-100.png")))
        authors = ["GNOME Documentation Team"]
        documenters = ["GNOME Documentation Team"]
        about_dialog.set_program_name(self.app)
        about_dialog.set_copyright(
            "Copyright \xa9 7527 \u0412\u043B\u0430\u0434\u0438\u043C\u0456\u0440\u044A")
        about_dialog.set_authors(authors)
        about_dialog.set_documenters(documenters)
        about_dialog.set_website("https://github.com/Vladimyr0/batterindicator")
        about_dialog.set_website_label("GitHub Repo Website")
        about_dialog.set_title(self.app)
        about_dialog.run()
        about_dialog.destroy()

    def message(self, source):
        args = ['/bin/sh','-c','upower -i $(upower -e | grep '+selected_device+')']
        mf = ''
        st = ''
        for line in subprocess.check_output(args).splitlines():
            sline = line.decode('Utf-8').strip()
            if sline.find('model:') >= 0: 
                mf = sline
            elif (sline.find('state:') >= 0) or (sline.find('battery-level:') >= 0) or (sline.find('percentage:') >= 0): 
                st += sline + '\n'
        messagedialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
            message_format=mf)
        messagedialog.format_secondary_text(st)
        messagedialog.set_title(self.app)
        messagedialog.connect("response", self.dialog_response)
        messagedialog.show()
        
    def dialog_response(self, widget, response_id):
        widget.destroy()

Indicator()
GObject.threads_init()
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
