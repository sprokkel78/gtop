import gi
import subprocess
import os
import datetime
import platform
import psutil
from gi.repository import Gtk, GLib, Pango
from threading import Thread
from time import sleep
gi.require_version('Gtk', '3.0')


# TODO


# VERSION 1.1.2
ver = "1.1.2"

# GLOBALS
pfilter = ""
pid = ""
pause = 0
nic_active = 0
services = 0
connections = 0
traffic_reset = 0
buffer = ""


# DEFINE HANDLER FUNCTIONS


def is_dark_mode_enabled():
    command = 'osascript -e "tell app \\"System Events\\" to tell appearance preferences to get dark mode"'
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = result.communicate()
    out = out.strip()
    if out == "true":
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
    else:
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", False)


def set_font_recursive(widget, fontdesc):
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            set_font_recursive(child, fontdesc)
    elif isinstance(widget, Gtk.Widget):
        widget.modify_font(fontdesc)


def Write_Header():
    txt = "\n\n    System Time - Uptime : "
    curr_date = datetime.date.today()
    txt = txt + curr_date.strftime("%Y-%m-%d")
    curr_time = datetime.datetime.now()
    txt = txt + " " + curr_time.strftime("%H:%M")
    txt = txt + " - "
    result = subprocess.Popen("uptime", shell=True, stdout=subprocess.PIPE)
    out = result.communicate()
    komma_split = str(out[0])
    sp_split = komma_split.split(",")
    ssp_split = sp_split[0].split("up")
    txt = txt + ssp_split[1].strip()
    txt = txt + "\n    System Users Online  : "
    result = subprocess.Popen("who | wc -l", shell=True, stdout=subprocess.PIPE)
    out = result.communicate()
    users = str(out[0]).split('\\n')
    user = users[0].split('b\'')
    number = user[1].strip()
    if int(number) == 1:
        txt = txt + str(number) + " user is logged in."
    else:
        txt = txt + str(number) + " users are logged in."

    global nic_active
    if nic_active != 0:
        if nic_active == 1:
            txt = txt + "\n    System Network Stats : " + str(nic_active) + " interface is active."
        if nic_active == 2:
            txt = txt + "\n    System Network Stats : " + str(nic_active) + " interfaces are active."
    else:
        txt = txt + "\n    System Network Cards : 0 interfaces are active."

    global services
    if services == "1":
        txt = txt + "\n    System Services TCP  : " + str(services) + " service is up."
    else:
        txt = txt + "\n    System Services TCP  : " + str(services) + " services are up."

    global connections
    if connections == "1":
        txt = txt + "\n    System Connections   : " + str(connections) + " socket is in use."
    else:
        txt = txt + "\n    System Connections   : " + str(connections) + " sockets are in use."

    txt = txt + "\n    System Load Averages : "
    load_avg = os.getloadavg()
    rounded_load_avg_a = round(load_avg[0], 2)
    rounded_load_avg_b = round(load_avg[1], 2)
    rounded_load_avg_c = round(load_avg[2], 2)
    txt = txt + str(rounded_load_avg_a) + " " + str(rounded_load_avg_b) + " " + str(rounded_load_avg_c)
    tcpu = subprocess.Popen("ps -A -o %cpu | awk '{s+=$1} END {print s}'", shell=True, stdout=subprocess.PIPE)
    out = tcpu.communicate()
    out = str(out[0]).split('b\'')
    out = str(out[1]).split('\\n')
    txt = txt + "\n    System Process List  : Total CPU usage " + str(out[0]) + "%\n\n"

    global buffer
    buffer = txt
    return txt


def get_process_list():
    global pfilter
    if pfilter == "":
        # print("filter is empty")
        result = subprocess.Popen("ps axu -c | head -n 101 | tail -n 100 | awk '{print $3, $11, $2, $1}'",
                                  shell=True,
                                  stdout=subprocess.PIPE)
        out = result.communicate()
        plist = str(out[0])
        plist = plist.split('\\n')
    else:
        # print(filter)
        if " " not in pfilter and ";" not in pfilter:
            result = subprocess.Popen("ps axu -c | grep " + pfilter
                                      + " | head -n 101 | tail -n 100 | awk '{print $3, $11, $2, $1}'", shell=True,
                                      stdout=subprocess.PIPE)

            out = result.communicate()
            plist = str(out[0])
            plist = plist.split('\\n')
        else:
            plist = " error in filter"

    return plist


def Update_Buffer(txt):
    global pause
    if pause == 0:
        tbuffer.set_text(txt)


def Update_System():
    i = 0
    while i == 0:
        txt = Write_Header()
        process_list = get_process_list()
        y = 0
        while y < len(process_list):
            if y == 0:
                if y < len(process_list):
                    res = process_list[y].split('b\'')
                    if len(res) >= 2:
                        proc = res[1]
                        txt = txt + "    " + str(proc) + "\n"
            else:
                if y < len(process_list):
                    if str(process_list[y]) != "'":
                        txt = txt + "    " + str(process_list[y]) + "\n"

            y = y + 1

        GLib.idle_add(Update_Buffer, txt)
        sleep(5)


def Update_Users():
    i = 0
    while i == 0:
        global buffer
        userlist = buffer

        result = subprocess.Popen("who", shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        txts = txt.split('\\n')
        y = 0
        userlist = userlist + "    USERS LOGGED IN: \n"
        while y < len(txts):
            user = txts[y]
            if y == 0:
                txtss = user.split('b\'')
                user = txtss[1]
            if user != "'":
                userlist = userlist + "\n    " + user
            y = y + 1

        GLib.idle_add(Update_Users_Buffer, userlist)
        sleep(5)


def Update_Users_Buffer(users):
    global pause
    if pause == 0:
        tbuffer_users.set_text(users)


def Update_Netstat():
    i = 0
    while i == 0:
        global buffer
        netlist = buffer

        result = subprocess.Popen("netstat -ltn | grep tcp4 | grep ESTAB | awk '{print $1, $4, $5, $6}'",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(str(txt))
        txts = txt.split('\\n')
        y = 0
        netlist = netlist + "    NETWORK CONNECTIONS:\n"
        while y < len(txts):
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
            if net != "'":
                netlist = netlist + "\n    " + net
            y = y + 1

        result = subprocess.Popen("netstat -ltn | grep tcp4 | grep ESTAB | wc -l",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(txt)
        global connections
        connections = 0
        if len(txt) > 0:
            txt_split = txt.split('b\'')
            txt_line = txt_split[1].split('\\n\'')
            connections = str(txt_line[0]).strip()
        # print(connections)
        GLib.idle_add(Update_Netstat_Buffer, netlist)
        sleep(5)


def Update_Netstat_Buffer(netstat):
    global pause
    if pause == 0:
        tbuffer_netstat.set_text(netstat)


def Update_Lsof():
    i = 0

    while i == 0:
        global services
        global nic_active
        global buffer
        lsoflist = buffer

        result = subprocess.Popen("lsof -i -n -P | grep TCP | grep IPv4 | awk '{print $1, $2, $3, $9, $10}'",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(str(txt))
        txts = txt.split('\\n')
        y = 0
        lsoflist = lsoflist + "    SOCKETS IPv4:\n"
        while y < len(txts):
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
            if net != "'":
                lsoflist = lsoflist + "\n    " + net
            y = y + 1
        result = subprocess.Popen("lsof -i -n -P | grep TCP | wc -l",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        service = str(out[0])
        services_split = service.split('b\'')
        services_line = services_split[1].split('\\n')
        # print(services_line[0].strip())
        services = 0
        services = services_line[0].strip()

        result = subprocess.Popen("lsof -i -n -P | grep TCP | grep IPv6 | awk '{print $1, $2, $3, $9, $10}'",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(str(txt))
        txts = txt.split('\\n')
        y = 0
        lsoflist = lsoflist + "\n\n\n    SOCKETS IPv6:\n"
        while y < len(txts):
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
            if net != "'":
                lsoflist = lsoflist + "\n    " + net
            y = y + 1

        GLib.idle_add(Update_Lsof_Buffer, lsoflist)
        sleep(5)


def Update_Lsof_Buffer(lsof):
    global pause
    if pause == 0:
        tbuffer_lsof.set_text(lsof)


def Update_Net():
    i = 0
    while i == 0:
        global nic_active
        global buffer
        netlist = buffer
        result = subprocess.Popen("ifconfig en0", shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(str(txt))
        txts = txt.split('\\n\\t')
        y = 0
        netlist = netlist + "    ETHERNET:\n "
        while y < len(txts):
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
            if y == len(txts) - 1:
                nnet = net.split('\\n')
                netlist = netlist + "\n    " + nnet[0]
            else:
                netlist = netlist + "\n    " + net

            y = y + 1
        nic_active = 0
        x = y - 1
        if x < len(txts):
            if "inactive" not in txts[x]:
                nic_active = nic_active + 1

        result = subprocess.Popen("ifconfig en1",
                                  shell=True, stdout=subprocess.PIPE)
        out = result.communicate()
        txt = str(out[0])
        # print(str(txt))
        txts = txt.split('\\n\\t')
        y = 0
        netlist = netlist + "\n\n\n    WIFI:\n"
        while y < len(txts):
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
            if y == len(txts) - 1:
                nnet = net.split('\\n')
                netlist = netlist + "\n    " + nnet[0]
            else:
                netlist = netlist + "\n    " + net
            y = y + 1
        x = y - 1
        if x < len(txts):
            if "inactive" not in txts[x]:
                nic_active = nic_active + 1

        result = subprocess.Popen("route -n get default | grep gateway",
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        # print(str(out))
        netlist = netlist + "\n\n\n    GATEWAY:\n"
        if len(str(out)) >= 0:
            txt = str(out)
            # print(str(txt))
            txts = txt.split('\\n\'')
            y = 0
            net = txts[y]
            if y == 0:
                txtss = net.split('b\'')
                net = txtss[1]
                if net != "'":
                    netlist = netlist + "\n    " + net.strip() + "\n"

        result = subprocess.Popen("route -n get default | grep interface",
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        if len(str(out)) >= 0:
            txt = str(out)
            # print(str(txt))
            txts = txt.split('\\n\'')
            y = 0
            # netlist = netlist + "\n"
            net = txts[y]
            if y == 0:
                # print(str(net))
                txtss = net.split('b\'')
                if len(txtss) > 0:
                    net = txtss[1]
                    if net != "'":
                        netlist = netlist + "\n    " + net.strip()

        GLib.idle_add(Update_Net_Buffer, netlist)
        sleep(5)


def Update_Net_Buffer(net):
    global pause
    if pause == 0:
        tbuffer_net.set_text(net)


def get_interface_bandwidth(interface_name):
    if_stats = psutil.net_if_stats()
    if interface_name in if_stats:
        net_io = psutil.net_io_counters(pernic=True)[interface_name]
        return net_io.bytes_sent, net_io.bytes_recv
    return None


def Update_Traffic():

    total_en0_out = 0
    total_en0_in = 0
    total_en1_out = 0
    total_en1_in = 0

    y = 0
    while y == 0:

        global buffer
        txt = buffer

        en0_bytes_send = 0
        en0_bytes_recv = 0
        en1_bytes_recv = 0
        en1_bytes_send = 0
        e0bs = 0
        e0br = 0
        e1bs = 0
        e1br = 0

        z = 0
        while z < 5:
            en0_bytes_sent_start, en0_bytes_recv_start = get_interface_bandwidth("en0")
            en1_bytes_sent_start, en1_bytes_recv_start = get_interface_bandwidth("en1")
            sleep(0.2)
            en0_bytes_sent_end, en0_bytes_recv_end = get_interface_bandwidth("en0")
            en1_bytes_sent_end, en1_bytes_recv_end = get_interface_bandwidth("en1")

            en0_bytes_send = en0_bytes_send + (en0_bytes_sent_end - en0_bytes_sent_start) / 1024
            e0bs = round(en0_bytes_send, 2)
            en0_bytes_recv = en0_bytes_recv + (en0_bytes_recv_end - en0_bytes_recv_start) / 1024
            e0br = round(en0_bytes_recv, 2)
            en1_bytes_send = en1_bytes_send + (en1_bytes_sent_end - en1_bytes_sent_start) / 1024
            e1bs = round(en1_bytes_send, 2)
            en1_bytes_recv = en1_bytes_recv + (en1_bytes_recv_end - en1_bytes_recv_start) / 1024
            e1br = round(en1_bytes_recv, 2)
            z = z + 1

        txt = txt + "    CURRENT USAGE:\n\n"
        txt = txt + "    Ethernet out : " + str(e0bs) + " KB/s\n"
        txt = txt + "    Ethernet in  : " + str(e0br) + " KB/s\n"
        txt = txt + "    Wifi out     : " + str(e1bs) + " KB/s\n"
        txt = txt + "    Wifi in      : " + str(e1br) + " KB/s\n"
        txt = txt + "\n"

        total_en0_out = round((total_en0_out + en0_bytes_send / 1024), 2)
        total_en0_in = round((total_en0_in + en0_bytes_recv / 1024), 2)
        total_en1_out = round((total_en1_out + en1_bytes_send / 1024), 2)
        total_en1_in = round((total_en1_in + en1_bytes_recv / 1024), 2)

        global traffic_reset

        if traffic_reset == 1:
            total_en0_out = 0.0
            total_en0_in = 0.0
            total_en1_out = 0.0
            total_en1_in = 0.0
            traffic_reset = 0

        txt = txt + "    TOTAL USAGE:\n\n"
        txt = txt + "    Ethernet out : " + str(total_en0_out) + " MB\n"
        txt = txt + "    Ethernet in  : " + str(total_en0_in) + " MB\n"
        txt = txt + "    Wifi out     : " + str(total_en1_out) + " MB\n"
        txt = txt + "    Wifi in      : " + str(total_en1_in) + " MB\n"

        GLib.idle_add(Update_Traffic_Buffer, txt)


def Update_Traffic_Buffer(traffic):
    global pause
    if pause == 0:
        tbuffer_traffic.set_text(traffic)


def filter_button_run_clicked(obj):
    global pfilter
    pfilter = entry1.get_text()


def filter_button_clear_clicked(obj):
    global pfilter
    pfilter = ""
    entry1.set_text("")


def button_pkill_clicked(obj):
    global pid
    pid = entry2.get_text()

    if pid != "" and pid.isdigit():
        result = subprocess.Popen("kill -9 " + pid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        # if "permitted" in str(err):
        #    print("Can't kill process: Permission Denied.")
        # else:
        #    print("Process killed.")


def button_clear_clicked(obj):
    global pid
    pid = ""
    entry2.set_text("")


def button_system_clicked(obj):
    container_system.show()
    container_users.hide()
    container_netstat.hide()
    container_lsof.hide()
    container_net.hide()
    container_traffic.hide()
    label1.set_text("SYSTEM")


def button_users_clicked(obj):
    container_users.show()
    container_system.hide()
    container_netstat.hide()
    container_lsof.hide()
    container_net.hide()
    container_traffic.hide()
    label1.set_text("USERS")


def button_netstat_clicked(obj):
    container_netstat.show()
    container_system.hide()
    container_users.hide()
    container_lsof.hide()
    container_net.hide()
    container_traffic.hide()
    label1.set_text("CONNECTIONS")


def button_lsof_clicked(obj):
    container_lsof.show()
    container_system.hide()
    container_users.hide()
    container_netstat.hide()
    container_net.hide()
    container_traffic.hide()
    label1.set_text("SERVICES")


def button_net_clicked(obj):
    container_net.show()
    container_system.hide()
    container_users.hide()
    container_netstat.hide()
    container_lsof.hide()
    container_traffic.hide()
    label1.set_text("NETWORK")


def button_traffic_clicked(obj):
    container_traffic.show()
    container_system.hide()
    container_users.hide()
    container_netstat.hide()
    container_lsof.hide()
    container_net.hide()
    label1.set_text("TRAFFIC")


def button_reset_traffic_clicked(obj):
    global traffic_reset
    traffic_reset = 1


def button_pause_clicked(obj):
    global pause
    if pause == 0:
        pause = 1
        button_pause.set_label("START")
    else:
        pause = 0
        button_pause.set_label("PAUSE")


# USER INTERFACE

# CREATE THE MAIN WINDOW
win = Gtk.Window()
win.set_title("gTop - " + ver)
win.set_default_size(800, 600)
win.connect("destroy", Gtk.main_quit)
win_w = 800
win_h = 600

# ACCOUNT FOR DARK MODE THEME
is_dark_mode_enabled()

# CREATE SOME SEPARATORS
sep1 = Gtk.Separator()
sep2 = Gtk.Separator()
sep3 = Gtk.Separator()
sep4 = Gtk.Separator()
sep5 = Gtk.Separator()

# CREATE THE GUI CONTAINER LAYOUT
box1 = Gtk.VBox(spacing=6)
win.add(box1)
box1.show()
boxsep1 = Gtk.Box(spacing=6)
boxsep1.pack_start(sep1, True, True, 0)
boxsep1.show()
box1.pack_start(boxsep1, False, False, 0)
box2 = Gtk.Box(spacing=6)
box1.pack_start(box2, False, False, 0)
box2.show()
boxsep2 = Gtk.Box(spacing=6)
boxsep2.pack_start(sep2, True, True, 0)
box1.pack_start(boxsep2, False, False, 0)
boxsep2.show()
box3 = Gtk.Box(spacing=6)
box1.pack_start(box3, False, False, 0)
box3.show()
boxsep3 = Gtk.Box(spacing=6)
boxsep3.pack_start(sep3, True, True, 0)
box1.pack_start(boxsep3, False, False, 0)
boxsep3.show()
box4 = Gtk.Box(spacing=6)
box1.pack_start(box4, True, True, 0)
box4.show()
box5 = Gtk.Box(spacing=6)
box1.pack_start(box5, False, False, 0)
box5.show()
box6 = Gtk.Box(spacing=6)
box1.pack_start(box6, False, False, 0)
box6.show()
box7 = Gtk.Box(spacing=6)
box7.pack_start(sep4, True, True, 0)
box1.pack_start(box7, False, False, 0)
box7.show()
box8 = Gtk.Box(spacing=6)
statusbar = Gtk.Statusbar()
box8.pack_start(statusbar, True, True, 0)
box1.pack_start(box8, False, False, 0)
box8.show()
statusbar.show()

label2 = Gtk.Label()
label2.set_width_chars(2)
box2.pack_start(label2, False, False, 0)
label2.show()

button_system = Gtk.Button.new_with_label("SYSTEM")
box2.pack_start(button_system, False, False, 0)
button_system.connect("clicked", button_system_clicked)
button_users = Gtk.Button.new_with_label("USERS")
button_users.connect("clicked", button_users_clicked)
box2.pack_start(button_users, False, False, 0)
button_net = Gtk.Button.new_with_label("NETWORK")
button_net.connect("clicked", button_net_clicked)
box2.pack_start(button_net, False, False, 0)
button_traffic = Gtk.Button.new_with_label("TRAFFIC")
button_traffic.connect("clicked", button_traffic_clicked)
box2.pack_start(button_traffic, False, False, 0)
button_lsof = Gtk.Button.new_with_label("SERVICES")
button_lsof.connect("clicked", button_lsof_clicked)
box2.pack_start(button_lsof, False, False, 0)
button_netstat = Gtk.Button.new_with_label("CONNECTIONS")
button_netstat.connect("clicked", button_netstat_clicked)
box2.pack_start(button_netstat, False, False, 0)
label_space = Gtk.Label()
box2.pack_start(label_space, True, True, 0)
button_pause = Gtk.Button.new_with_label("PAUSE")
button_pause.connect("clicked", button_pause_clicked)
box2.pack_start(button_pause, False, False, 0)
label_end = Gtk.Label()
label_end.set_width_chars(2)
box2.pack_start(label_end, False, False, 0)
button_system.show()
button_users.show()
button_net.show()
button_netstat.show()
button_lsof.show()
button_traffic.show()
label_space.show()
button_pause.show()
label_end.show()

label0 = Gtk.Label()
label0.set_width_chars(4)
box3.pack_start(label0, False, False, 0)
label0.show()
label1 = Gtk.Label()
label1.set_text("SYSTEM")
box3.pack_start(label1, False, False, 0)
label1.show()

container_system = Gtk.VBox()
box4.pack_start(container_system, True, True, 0)
container_system.show()

container_users = Gtk.VBox()
box4.pack_start(container_users, True, True, 0)
container_users.hide()

container_netstat = Gtk.VBox()
box4.pack_start(container_netstat, True, True, 0)
container_netstat.hide()

container_lsof = Gtk.VBox()
box4.pack_start(container_lsof, True, True, 0)
container_lsof.hide()

container_net = Gtk.VBox()
box4.pack_start(container_net, True, True, 0)
container_net.hide()

container_traffic = Gtk.VBox()
box4.pack_start(container_traffic, True, True, 0)
container_traffic.hide()

# SYSTEM TAB
box9 = Gtk.Box(spacing=6)
container_system.pack_start(box9, True, True, 0)
scrolled_window = Gtk.ScrolledWindow()
scrolled_window.set_size_request(win_w, win_h)
tbuffer = Gtk.TextBuffer()
textview = Gtk.TextView.new_with_buffer(tbuffer)
textview.set_size_request(win_w, win_h)
textview.set_editable(False)
textview.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window.add(textview)
box9.pack_start(scrolled_window, True, True, 0)
box9.show()
scrolled_window.show()
textview.show()
box10 = Gtk.Box(spacing=6)
container_system.pack_start(box10, False, False, 0)
box10.show()
label4 = Gtk.Label()
box10.pack_start(label4, False, False, 0)
label4.show()
box11 = Gtk.Box(spacing=6)
container_system.pack_start(box11, False, False, 0)
box11.show()
label3 = Gtk.Label()
label3.set_text("     Filter Process ")
box11.pack_start(label3, False, False, 0)
label3.show()
entry1 = Gtk.Entry()
entry1.set_width_chars(13)
entry1.set_max_length(13)
box11.pack_start(entry1, False, False, 0)
entry1.show()
button2 = Gtk.Button.new_with_label("  Filter  ")
button2.connect("clicked", filter_button_run_clicked)
box11.pack_start(button2, False, False, 0)
button2.show()
button3 = Gtk.Button.new_with_label("  Clear  ")
button3.connect("clicked", filter_button_clear_clicked)
box11.pack_start(button3, False, False, 0)
button3.show()
box12 = Gtk.Box(spacing=6)
container_system.pack_start(box12, False, False, 0)
box12.show()
label4 = Gtk.Label()
label4.set_text("     End Proc_PID   ")
box12.pack_start(label4, False, False, 0)
label4.show()
entry2 = Gtk.Entry()
entry2.set_width_chars(13)
entry2.set_max_length(13)
box12.pack_start(entry2, False, False, 0)
entry2.show()
button4 = Gtk.Button.new_with_label("   Kill   ")
button4.connect("clicked", button_pkill_clicked)
box12.pack_start(button4, False, False, 0)
button4.show()
button5 = Gtk.Button.new_with_label("  Clear  ")
button5.connect("clicked", button_clear_clicked)
box12.pack_start(button5, False, False, 0)
button5.show()


# USERS TAB
box13 = Gtk.Box(spacing=6)
container_users.pack_start(box13, True, True, 0)
box13.show()
scrolled_window_users = Gtk.ScrolledWindow()
scrolled_window_users.set_size_request(win_w, win_h)
tbuffer_users = Gtk.TextBuffer()
textview_users = Gtk.TextView.new_with_buffer(tbuffer_users)
textview_users.set_size_request(win_w, win_h)
textview_users.set_editable(False)
textview_users.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window_users.add(textview_users)
box13.pack_start(scrolled_window_users, True, True, 0)
scrolled_window_users.show()
textview_users.show()


# CONNECTIONS TAB
box14 = Gtk.Box(spacing=6)
container_netstat.pack_start(box14, True, True, 0)
box14.show()
scrolled_window_netstat = Gtk.ScrolledWindow()
scrolled_window_netstat.set_size_request(win_w, win_h)
tbuffer_netstat = Gtk.TextBuffer()
textview_netstat = Gtk.TextView.new_with_buffer(tbuffer_netstat)
textview_netstat.set_size_request(win_w, win_h)
textview_netstat.set_editable(False)
textview_netstat.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window_netstat.add(textview_netstat)
box14.pack_start(scrolled_window_netstat, True, True, 0)
scrolled_window_netstat.show()
textview_netstat.show()


# SERVICES TAB
box15 = Gtk.Box(spacing=6)
container_lsof.pack_start(box15, True, True, 0)
box15.show()
scrolled_window_lsof = Gtk.ScrolledWindow()
scrolled_window_lsof.set_size_request(win_w, win_h)
tbuffer_lsof = Gtk.TextBuffer()
textview_lsof = Gtk.TextView.new_with_buffer(tbuffer_lsof)
textview_lsof.set_size_request(win_w, win_h)
textview_lsof.set_editable(False)
textview_lsof.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window_lsof.add(textview_lsof)
box15.pack_start(scrolled_window_lsof, True, True, 0)
scrolled_window_lsof.show()
textview_lsof.show()


# NETWORK TAB
box16 = Gtk.Box(spacing=6)
container_net.pack_start(box16, True, True, 0)
box16.show()
scrolled_window_net = Gtk.ScrolledWindow()
scrolled_window_net.set_size_request(win_w, win_h)
tbuffer_net = Gtk.TextBuffer()
textview_net = Gtk.TextView.new_with_buffer(tbuffer_net)
textview_net.set_size_request(win_w, win_h)
textview_net.set_editable(False)
textview_net.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window_net.add(textview_net)
box16.pack_start(scrolled_window_net, True, True, 0)
scrolled_window_net.show()
textview_net.show()

# TRAFFIC TAB
box17 = Gtk.Box(spacing=6)
container_traffic.pack_start(box17, True, True, 0)
box17.show()
scrolled_window_traffic = Gtk.ScrolledWindow()
scrolled_window_traffic.set_size_request(win_w, win_h)
tbuffer_traffic = Gtk.TextBuffer()
textview_traffic = Gtk.TextView.new_with_buffer(tbuffer_traffic)
textview_traffic.set_size_request(win_w, win_h)
textview_traffic.set_editable(False)
textview_traffic.modify_font(Pango.FontDescription.from_string("Monospace 16"))
scrolled_window_traffic.add(textview_traffic)
box17.pack_start(scrolled_window_traffic, True, True, 0)
scrolled_window_traffic.show()
textview_traffic.show()
box18 = Gtk.Box(spacing=6)
container_traffic.pack_start(box18, True, False, 0)
box18.show()
label5_space = Gtk.Label()
label5_space.set_width_chars(4)
box18.pack_start(label5_space, False, False, 0)
label5_space.show()
label5 = Gtk.Label()
label5.set_text("Reset Counter ")
box18.pack_start(label5, False, False, 0)
label5.show()
button_reset_traffic = Gtk.Button.new_with_label("Reset")
button_reset_traffic.connect("clicked", button_reset_traffic_clicked)
box18.pack_start(button_reset_traffic, False, False, 0)
button_reset_traffic.show()


# PUSH MAC VERSION TO STATUSBAR
mac_version = platform.mac_ver()
statusbar.push(0, "   MacOS Version: " + mac_version[0])


# RUN THREADS
thread_users = Thread(target=Update_Users)
thread_users.daemon = True
thread_users.start()

thread_netstat = Thread(target=Update_Netstat)
thread_netstat.daemon = True
thread_netstat.start()

thread_lsof = Thread(target=Update_Lsof)
thread_lsof.daemon = True
thread_lsof.start()

thread_net = Thread(target=Update_Net)
thread_net.daemon = True
thread_net.start()

thread_system = Thread(target=Update_System)
thread_system.daemon = True
thread_system.start()

thread_traffic = Thread(target=Update_Traffic)
thread_traffic.daemon = True
thread_traffic.start()

# SET THE DEFAULT FONT FOR ALL WIDGETS
font_desc = Pango.FontDescription.from_string("Monospace 14")
set_font_recursive(win, font_desc)


# START THE APPLICATION
win.show()
Gtk.main()
