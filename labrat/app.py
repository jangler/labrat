import argparse
import math
import os.path
import sys
import traceback

import tkinter as tk
import tkinter.messagebox

from labrat.catcher import Catcher
import labrat.convert as convert

VERSION = [0, 0, 0]


def signature():
    return '{} {}.{}.{}'.format(os.path.basename(sys.argv[0]), *VERSION)


ABOUT = """{}

http://jangler.info/code/labrat""".format(signature())


class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.updating = False
        self.create_widgets()
        self.pack(expand=1, fill='both')
        master.protocol("WM_DELETE_WINDOW", self.quit)
        master.title(signature())

    def create_scale(self, master, label, from_, to, initial, hs):
        # determine which commands to associate
        if hs:
            scale_update = self.hs_scale_update
            entry_update = self.hs_entry_update
        else:
            scale_update = self.lab_scale_update
            entry_update = self.lab_entry_update

        # create widgets
        frame = tk.Frame(master)
        tk.Label(frame, text=label, width=3).pack(side='left')
        scale = tk.Scale(frame, from_=from_, to=to, showvalue=0,
                         orient='horizontal', command=scale_update)
        scale.pack(side='left')
        var = tk.StringVar()
        var.set(initial)
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
            self.create_scale(control_frame, 'L*', 0, 100, 50, False)
        self.ascale, self.aentry = \
            self.create_scale(control_frame, 'a*', -100, 100, 0, False)
        self.bscale, self.bentry = \
            self.create_scale(control_frame, 'b*', -100, 100, 0, False)
        self.hscale, self.hentry = \
            self.create_scale(control_frame, 'Hue', 0, 360, 0, True)
        self.sscale, self.sentry = \
            self.create_scale(control_frame, 'Sat', 0, 100, 0, True)

        # associate entries with their corresponding scales
        self.control_dict = {
            self.lentry: self.lscale,
            self.aentry: self.ascale,
            self.bentry: self.bscale,
            self.hentry: self.hscale,
            self.sentry: self.sscale
        }

        # create RGB control
        rgb_frame = tk.Frame(control_frame)
        tk.Label(rgb_frame, text='RGB').pack(side='left')
        rgb_var = tk.StringVar()
        rgb_var.trace('w', self.rgb_update)
        self.rgb_entry = tk.Entry(rgb_frame, width=8, textvariable=rgb_var)
        self.rgb_entry.pack(side='left')
        rgb_frame.pack(anchor='e')

        control_frame.pack(anchor='n', side='left')

        # set initial preview color
        self.lab_entry_update()

        main_frame.pack(expand=1, fill='both')

    def rgb_update(self, *args):
        if self.updating or len(self.rgb_entry.get()) != 7:
            return

        try:
            val = int(self.rgb_entry.get()[1:], 16)
        except ValueError:
            return

        # convert int to LAB
        rgb = convert.rgb_from_int(val)
        xyz = convert.xyz_from_rgb(rgb)
        lab = convert.lab_from_xyz(xyz)

        # update LAB entries
        for i, entry in enumerate([self.lentry, self.aentry, self.bentry]):
            if entry.get() != str(round(lab[i])):
                entry.delete(0, 'end')
                entry.insert(0, str(round(lab[i])))

    def entry_update(self):
        # update scales
        for entry, scale in self.control_dict.items():
            try:
                val = int(entry.get())
                scale.set(val)
            except ValueError:
                pass

        # convert LAB to int
        lab = tuple([self.lscale.get(), self.ascale.get(), self.bscale.get()])
        xyz = convert.xyz_from_lab(lab)
        rgb = convert.rgb_from_xyz(xyz)
        val = convert.int_from_rgb(rgb)

        # update color preview and RGB entry
        hex_str = '#{}'.format(hex(val)[2:].rjust(6, '0'))
        self.preview.config(bg=hex_str)
        if self.rgb_entry.get() != hex_str:
            self.rgb_entry.delete(0, 'end')
            self.rgb_entry.insert(0, hex_str)

    def lab_entry_update(self, *args):
        if self.updating:
            return
        self.updating = True

        # set hue and sat based on a* and b*
        lab = tuple([self.lscale.get(), self.ascale.get(), self.bscale.get()])
        hue = str(round(math.degrees(math.atan2(lab[2], lab[1])) % 360))
        if self.hentry.get() != hue:
            self.hentry.delete(0, 'end')
            self.hentry.insert(0, hue)
        sat = str(round(math.hypot(lab[1], lab[2]) / 1.41))
        if self.sentry.get() != sat:
            self.sentry.delete(0, 'end')
            self.sentry.insert(0, sat)

        self.entry_update()
        self.updating = False

    def hs_entry_update(self, *args):
        if self.updating:
            return
        self.updating = True

        # set a* and b* based on hue and sat
        try:
            hue = math.radians(int(self.hentry.get()))
            sat = int(self.sentry.get()) * 1.41
            a = str(round(math.cos(hue) * sat))
            b = str(round(math.sin(hue) * sat))
            if self.aentry.get() != a:
                self.aentry.delete(0, 'end')
                self.aentry.insert(0, a)
            if self.bentry.get() != b:
                self.bentry.delete(0, 'end')
                self.bentry.insert(0, b)
        except ValueError:
            pass

        self.entry_update()
        self.updating = False

    def error(self, err):
        self.state()
        traceback.print_exc()
        tkinter.messagebox.showerror(type(err).__name__, str(err))

    def quit(self, event=None):
        super().quit()

    def scale_update(self):
        modified = False
        for entry, scale in self.control_dict.items():
            if entry.get() and entry.get() != str(scale.get()):
                modified = True
                entry.delete(0, 'end')
                entry.insert(0, str(scale.get()))
        return modified

    def lab_scale_update(self, event=None):
        if self.scale_update():
            self.lab_entry_update()

    def hs_scale_update(self, event=None):
        if self.scale_update():
            self.hs_entry_update()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=signature())
    return parser.parse_args()


def main():
    args = parse_args()

    # create app and display tkinter exceptions in message boxes
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
