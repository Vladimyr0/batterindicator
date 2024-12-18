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
usage = 'usage: "batterindicator.py -k/m [-d/w] [-p] [--l=N]"'

class Indicator():

    def __init__(self):
        global device_icon, show_percentage, selected_theme, warning_limit, args, lp, perc
        selected_device = ''
        device_icon = ''
        show_percentage = False
        selected_theme = 'd'
        warning_limit = 10
        args = []
        lp = 100
        perc = '??'
        try:
            opts, args = getopt.getopt(sys.argv[1:],"kmdwp",["l="])
        except getopt.GetoptError:
            print (usage)
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-k':
                selected_device = 'battery_hidpp_battery_0'
                device_icon = 'kbd'
            elif opt == '-m':
                selected_device = 'battery_hidpp_battery_1'
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
                    warning_limit = 5
        if selected_device == '':
            print (usage)
            sys.exit(2)

        self.app = 'batterindicator'
        args = ['/bin/sh','-c','upower -i $(upower -e | grep '+selected_device+')']
        self.indicator = AppIndicator3.Indicator.new(
            self.app, 
            os.path.join(os.path.abspath (os.path.dirname(sys.argv[0])), icon_folder+"/bat_"+device_icon+"_"+selected_theme+"_nn.png"),
            AppIndicator3.IndicatorCategory.HARDWARE)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())
        if show_percentage:
            self.indicator.set_label("? %", self.app)
        Notify.init(self.app)
        self.update = Thread(target=self.show_perc)
        self.update.setDaemon(True)
        self.update.start()

    def create_menu(self):
        menu = Gtk.Menu()
        item_about = Gtk.ImageMenuItem('about')
        about_img = Gtk.Image()
        about_img.set_from_icon_name("help-about", Gtk.IconSize.MENU)
        item_about.set_image(about_img)
        item_about.set_always_show_image(True)
        item_about.connect('activate', self.about)
        menu.append(item_about)
        menu_sep = Gtk.SeparatorMenuItem()
        menu.append(menu_sep)
        item_info = Gtk.ImageMenuItem('info')
        info_img = Gtk.Image()
        info_img.set_from_icon_name("tray-message", Gtk.IconSize.MENU)
        item_info.set_image(info_img)
        item_info.set_always_show_image(True)
        item_info.connect('activate', self.message)
        menu.append(item_info)
        menu_sep = Gtk.SeparatorMenuItem()
        menu.append(menu_sep)
        item_quit = Gtk.ImageMenuItem("quit")
        copy_img = Gtk.Image()
        copy_img.set_from_icon_name("application-exit", Gtk.IconSize.MENU)
        item_quit.set_image(copy_img)
        item_quit.set_always_show_image(True)
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)
        menu.show_all()
        return menu

    def show_perc(self):
        global device_icon, show_percentage, selected_theme, warning_limit, args, lp, perc
        time.sleep(3)
        while True:
            model = ''
            m = ''
            disc = False
            unkn = False
            full = False
            perc_ = ''
            try:
                s = subprocess.check_output(args).decode('Utf-8')
            except subprocess.CalledProcessError:
                s = ''                
            for line in s.splitlines():
                sline = line.strip()
                if sline.find ('model:') >= 0:
                    model = sline[22:]
                elif (sline.find ('state:') >= 0) and (sline.find('unknown') >= 0):
                    m = 'm'
                elif (sline.find ('state:') >= 0) and ((sline.find(' charg') >= 0) or (sline.find('full') >= 0)):
                    m = 'c'
                    if sline.find('full') >= 0:
                        perc = '100'
                        full = True
                elif (sline.find ('state:') >= 0) and (sline.find('discharg') >= 0):
                    disc = True
                elif sline.find ('percentage:') >= 0:
                    perc_ = sline[21:(sline.find ('%'))]
                elif (sline.find ('battery-level:') >= 0) and (sline.find ('unknown') >= 0):
                    unkn = True
                    if disc: perc = '1'
                if (perc_ != '') and not unkn: perc = perc_
            try:
                p = int (perc)
            except ValueError:
                p = -1
            iname = {
                90 < p <= 100: "100",
                60 < p <= 90: "80",
                10 < p <= 60: "60",
                5 < p <= 10: "40",
                0 <= p <= 5: "20",
                p < 0: "nn"
            }[True]            
            if show_percentage:
                if (m == '') or full:
                    plabel = perc+"%"
                else:
                    plabel = perc.replace("0","\u2080").replace("1","\u2081").replace("2","\u2082").replace("3","\u2083").replace("4","\u2084").replace("5","\u2085").replace("6","\u2086").replace("7","\u2087").replace("8","\u2088").replace("9","\u2089")+"\uFE6A"
                GObject.idle_add(self.indicator.set_label, plabel, self.app,  priority=GObject.PRIORITY_DEFAULT)
            GObject.idle_add(self.indicator.set_icon, 
                os.path.join(os.path.abspath (os.path.dirname(sys.argv[0])), icon_folder+"/bat_"+device_icon+"_"+selected_theme+m+"_"+iname+".png"),
            priority=GObject.PRIORITY_DEFAULT)
            if (0 <= p < warning_limit) and (lp >= warning_limit):
                Notify.Notification.new("<b>"+model+"</b>", 
                    "\u0411\u0430\u0442\u0430\u0440\u0435\u044F \u0440\u0430\u0437\u0440\u044F\u0436\u0435\u043D\u0430!", 
                os.path.join(os.path.abspath (os.path.dirname(sys.argv[0])), icon_folder+"/battery-charge-20.png")).show()    
            lp = p
            time.sleep(30)

    def stop(self, source):
        Gtk.main_quit()

    def about(self, source):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(os.path.abspath (os.path.dirname(sys.argv[0])), icon_folder+"/battery-charge-100.png")))
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
        mf = ''
        st = ''
        s = ''
        try:
            s = subprocess.check_output(args, stderr=subprocess.STDOUT).decode('Utf-8')
        except subprocess.CalledProcessError as e:
            mf = 'ERROR'
            st = 'code: '+str(e.returncode)+'\n'+e.output.decode('Utf-8')
        if mf == '':
            for line in s.splitlines():
                sline = line.strip()
                if sline.find('model:') >= 0: 
                    mf = sline
                elif (sline.find('state:') >= 0) or (sline.find('battery-level:') >= 0):
                    st += sline + '\n'
                elif (sline.find('percentage:') >= 0):
                    st += sline[0:(sline.find ('%') + 1)] + '\n'
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
