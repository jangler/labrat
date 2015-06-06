import argparse
import functools
import math
import os.path
import sys
import traceback

import tkinter as tk
import tkinter.messagebox

from labrat.catcher import Catcher
import labrat.convert as convert

VERSION = [0, 0, 0]


def canonicalize_int(s):
    try:
        return str(int(s))
    except ValueError:
        return s


def int_or_zero(s):
    try:
        return int(s)
    except ValueError:
        return 0


def rgb_accept(c):
    return c.isdigit() or c == '#' or ('a' <= c.lower() <= 'f')


def signature():
    return '{} {}.{}.{}'.format(os.path.basename(sys.argv[0]), *VERSION)


def validate_entry(entry, accept, transform, minimum, maximum):
    s = transform(''.join(ch for ch in entry.get() if accept(ch)))

    try:
        if int(s) < minimum:
            s = str(minimum)
        elif int(s) > maximum:
            s = str(maximum)
    except ValueError:
        pass

    if s != entry.get():
        entry.delete(0, 'end')
        entry.insert(0, s)


ABOUT = """{}

http://jangler.info/code/labrat""".format(signature())


class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.synced = True
        self.l = 50
        self.a = self.b = self.hue = self.sat = 0
        self.create_widgets()
        self.pack(expand=1, fill='both')
        master.protocol("WM_DELETE_WINDOW", self.quit)
        master.title(signature())

    def getl(self): return self.l

    def geta(self): return self.a

    def getb(self): return self.b

    def gethue(self): return self.hue

    def getsat(self): return self.sat

    def create_scale(self, master, label, from_, to, hs, name):
        # determine which commands to associate
        if hs:
            scale_update = functools.partial(self.hs_scale_update, name)
            entry_update = self.hs_entry_update
        else:
            scale_update = functools.partial(self.lab_scale_update, name)
            entry_update = self.lab_entry_update

        # create widgets
        frame = tk.Frame(master)
        tk.Label(frame, text=label, width=3).pack(side='left')
        scale = tk.Scale(frame, from_=from_, to=to, showvalue=0,
                         orient='horizontal', command=scale_update)
        scale.pack(side='left')
        var = tk.StringVar(name=name)
        var.trace('w', entry_update)
        entry = tk.Entry(frame, width=4, textvariable=var)
        entry.pack(side='left')
        frame.pack()

        return scale, entry

    def create_widgets(self):
        main_frame = tk.Frame(self, bd=2)

        # create color preview
        self.preview = tk.Frame(main_frame, width=100)
        self.preview.pack(side='left', expand=1, fill='both')

        tk.Frame(main_frame, width=2).pack(side='left')  # pad

        control_frame = tk.Frame(main_frame)

        # create L*a*b* controls
        self.lscale, self.lentry = \
            self.create_scale(control_frame, 'L*', 0, 100, False, 'l')
        self.ascale, self.aentry = \
            self.create_scale(control_frame, 'a*', -100, 100, False, 'a')
        self.bscale, self.bentry = \
            self.create_scale(control_frame, 'b*', -100, 100, False, 'b')
        self.hscale, self.hentry = \
            self.create_scale(control_frame, 'Hue', 0, 360, True, 'hue')
        self.sscale, self.sentry = \
            self.create_scale(control_frame, 'Sat', 0, 100, True, 'sat')

        # associate entries with their corresponding values
        self.control_dict = {
            tuple([self.lscale, self.lentry]): self.getl,
            tuple([self.ascale, self.aentry]): self.geta,
            tuple([self.bscale, self.bentry]): self.getb,
            tuple([self.hscale, self.hentry]): self.gethue,
            tuple([self.sscale, self.sentry]): self.getsat,
        }

        # create RGB control
        rgb_frame = tk.Frame(control_frame)
        self.clip_label = tk.Label(control_frame, anchor='w')
        self.clip_label.pack(side='left')
        rgb_var = tk.StringVar(name='rgb')
        rgb_var.trace('w', self.rgb_update)
        self.rgb_entry = tk.Entry(rgb_frame, width=8, textvariable=rgb_var)
        self.rgb_entry.pack(side='right')
        tk.Label(rgb_frame, text='RGB').pack(side='right')
        rgb_frame.pack(anchor='e')

        control_frame.pack(anchor='n', side='left')

        # set initial preview color
        self.update_rgb()

        main_frame.pack(expand=1, fill='both')

    def rgb_update(self, *args):
        if not self.synced:
            return
        self.synced = False

        validate_entry(self.rgb_entry, rgb_accept,
                       lambda s: '#' + s[1:7].replace('#', ''), 0, 0)

        if len(self.rgb_entry.get()) != 7:
            self.synced = True
            return

        self.rgb = int(self.rgb_entry.get()[1:], 16)

        # convert int to LAB, update values and entries
        rgb = convert.rgb_from_int(self.rgb)
        xyz = convert.xyz_from_rgb(rgb)
        self.l, self.a, self.b = convert.lab_from_xyz(xyz)
        self.hue = math.degrees(math.atan2(self.b, self.a)) % 360
        self.sat = math.hypot(self.a, self.b) / math.hypot(1, 1)
        self.update_entries()
        self.update_rgb()

    def update_rgb(self):
        # convert LAB to int
        lab = [self.l, self.a, self.b]
        xyz = convert.xyz_from_lab(lab)
        rgb, clipped = convert.rgb_from_xyz(xyz)
        val = convert.int_from_rgb(rgb)

        # update clip indicator, color preview, and RGB entry
        self.clip_label.config(text='(clipped)' if clipped else '')
        hex_str = '#{}'.format(hex(val)[2:].rjust(6, '0'))
        self.preview.config(bg=hex_str)
        if self.rgb_entry.get() != hex_str:
            self.rgb_entry.delete(0, 'end')
            self.rgb_entry.insert(0, hex_str)

        # by now all values should be synchronized
        self.synced = True

    def update_hs(self):
        self.hue = math.degrees(math.atan2(self.b, self.a)) % 360
        self.sat = math.hypot(self.a, self.b) / math.hypot(1, 1)
        if self.hentry.get() != str(round(self.hue)):
            self.hentry.delete(0, 'end')
            self.hentry.insert(0, str(round(self.hue)))
        if self.sentry.get() != str(round(self.sat)):
            self.sentry.delete(0, 'end')
            self.sentry.insert(0, str(round(self.sat)))

    def lab_entry_update(self, name, index, mode):
        if not self.synced:
            return
        self.synced = False

        if name == 'l':
            validate_entry(self.lentry, str.isdigit, canonicalize_int, 0, 100)
            self.l = int_or_zero(self.lentry.get())
        elif name == 'a':
            validate_entry(self.aentry, lambda c: c.isdigit() or c == '-',
                           lambda s: canonicalize_int(s[:1] +
                                                      s[1:].replace('-', '')),
                           -100, 100)
            self.a = int_or_zero(self.aentry.get())
        elif name == 'b':
            validate_entry(self.bentry, lambda c: c.isdigit() or c == '-',
                           lambda s: canonicalize_int(s[:1] +
                                                      s[1:].replace('-', '')),
                           -100, 100)
            self.b = int_or_zero(self.bentry.get())

        self.update_hs()
        self.update_rgb()

    def update_ab(self):
        hue = math.radians(self.hue)
        sat = self.sat * math.hypot(1, 1)
        self.a = math.cos(hue) * sat
        self.b = math.sin(hue) * sat
        if self.aentry.get() != str(round(self.a)):
            self.aentry.delete(0, 'end')
            self.aentry.insert(0, str(round(self.a)))
        if self.bentry.get() != str(round(self.b)):
            self.bentry.delete(0, 'end')
            self.bentry.insert(0, str(round(self.b)))

    def hs_entry_update(self, name, index, mode):
        if not self.synced:
            return
        self.synced = False

        if name == 'hue':
            validate_entry(self.hentry, str.isdigit, canonicalize_int, 0, 360)
            self.hue = int_or_zero(self.hentry.get())
        elif name == 'sat':
            validate_entry(self.sentry, str.isdigit, canonicalize_int, 0, 100)
            self.sat = int_or_zero(self.sentry.get())

        self.update_ab()
        self.update_rgb()

    def error(self, err):
        self.state()
        traceback.print_exc()
        tkinter.messagebox.showerror(type(err).__name__, str(err))

    def quit(self, event=None):
        super().quit()

    def update_entries(self):
        for controls, accessor in self.control_dict.items():
            scale, entry = controls
            if scale.get() != accessor():
                scale.set(accessor())
            if entry.get() != str(round(accessor())):
                entry.delete(0, 'end')
                entry.insert(0, str(round(accessor())))

    def lab_scale_update(self, name, event):
        if not self.synced:
            return
        self.synced = False

        if name == 'l':
            self.l = self.lscale.get()
        elif name == 'a':
            self.a = self.ascale.get()
        elif name == 'b':
            self.b = self.bscale.get()

        self.update_hs()
        self.update_entries()
        self.update_rgb()

    def hs_scale_update(self, name, event):
        if not self.synced:
            return
        self.synced = False

        if name == 'hue':
            self.hue = self.hscale.get()
        elif name == 'sat':
            self.sat = self.sscale.get()

        self.update_ab()
        self.update_entries()
        self.update_rgb()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=signature())
    return parser.parse_args()


def main():
    args = parse_args()

    # create app and catch tkinter exceptions in message boxes
    tk.CallWrapper = Catcher
    app = App(tk.Tk())

    # display python exceptions in message boxes
    def excepthook(exctype, value, traceback):
        app.error(value)
    sys.excepthook = excepthook

    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.quit()
