"""
   Impedance Analyzer 
   Author:  Lars Lindner
   Revision:  25/03/2021

   -> This programm does a linear frequency sweep from 'freq_start' to 'freq_end' with 'freq_delta' using a GUI interface
   -> It prints the numerical values of frequency [Hz], impedance [Ohm] and phase [deg] as a txt-file
"""


import tkinter as tk
from tkinter import ttk
from tkinter import *

from ctypes import *
from dwfconstants import *

import math
import time
import sys
import numpy as np
import matplotlib.pyplot as plt


# region Init
# Default values for parameters
freq_start = int(3.5e6)
freq_end = int(4.5e6)
freq_delta = int(10000)
amp_start = float(0.1)
amp_end = float(0.3)
amp_delta = float(0.1)
resistance = int(1000)

# Variables Definitons
win = Tk()
hdwf = c_int()
sts = c_byte()
impedance = c_double()
phase = c_double()

# Load .dll
if sys.platform.startswith("win"):
    dwf = cdll.LoadLibrary("dwf.dll")
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")
# endregion


# region Window Functions
def connectFunction():
    connectButton.update()
    szerr = create_string_buffer(512)
    dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

    if hdwf.value == hdwfNone.value:
        dwf.FDwfGetLastErrorMsg(szerr)
        infoOutput.insert(tk.INSERT, str(szerr.value) + "\n")
        infoOutput.see("end")
    else:
        connectButton["state"] = tk.DISABLED
        disconnectButton["state"] = tk.NORMAL
        startButton["state"] = tk.NORMAL
        setButton["state"] = tk.NORMAL
        infoOutput.insert(tk.INSERT, "AD2 connected\n")
        infoOutput.see("end")


def disconnectFunction():
    disconnectButton.update()
    dwf.FDwfDeviceClose(hdwf)
    connectButton["state"] = tk.NORMAL
    disconnectButton["state"] = tk.DISABLED
    startButton["state"] = tk.DISABLED
    setButton["state"] = tk.DISABLED
    infoOutput.insert(tk.INSERT, "AD2 disconnected\n")
    infoOutput.see("end")


def setFunction():
    setButton.update()  # So the button 'Set Parameters' doesn't get blocked
    global freq_start
    global freq_end
    global freq_delta
    global resistance
    global amp_start
    freq_start = int(startFreqInput.get())
    freq_end = int(endFreqInput.get())
    freq_delta = int(deltaFreqInput.get())
    resistance = int(resistanceInput.get())
    amp_start = float(startAmpInput.get())
    amp_end = float(endAmpInput.get())
    amp_delta = float(deltaAmpInput.get())

    dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(3))  # this option will enable dynamic adjustment of analog out settings like: frequency, amplitude...
    dwf.FDwfAnalogImpedanceReset(hdwf)
    dwf.FDwfAnalogImpedanceModeSet(hdwf, c_int(8))  # 0 = W1-C1-DUT-C2-R-GND, 1 = W1-C1-R-C2-DUT-GND, 8 = AD IA adapter
    # dwf.FDwfAnalogImpedanceFrequencySet(hdwf, c_double(freq_start))  # frequency in Hertz
    dwf.FDwfAnalogImpedanceReferenceSet(hdwf, c_double(resistance))  # reference resistor value in Ohms
    # dwf.FDwfAnalogImpedanceAmplitudeSet(hdwf, c_double(amp_start))  # Measurement amplitude, 0V to peak signal
    time.sleep(1)

    infoOutput.insert(tk.INSERT, "All Parameters set\n")
    infoOutput.see("end")


def startFunction():
    startButton.update()
    infoOutput.insert(tk.INSERT, "Start Measurement:" + str(amp_start) + "V \n")
    infoOutput.update()                                 # Forces the GUI to update the text box

    initial = time.time()                               # Take time stamp

    dwf.FDwfAnalogImpedanceConfigure(hdwf, c_int(1))    # Measurement Start

    for amp in range(amp_start, amp_end, amp_delta):                       # Runs all the amplitude range

        extfile = open("impedance_" + str(amp) + "V_" + str(resistance) + "Ohm.txt", "w")
        dwf.FDwfAnalogImpedanceAmplitudeSet(hdwf, c_double(amp_start))      # Sets the stimulus amplitude (0V to peak signal)

        for freq in range(freq_start, freq_end + 1, freq_delta):            # Runs all the frequency range
            dwf.FDwfAnalogImpedanceFrequencySet(hdwf, c_double(freq))       # Sets the stimulus frequency
            time.sleep(0.01)                                                # Settle time of device under test (DUT), this value depends on the device!
            dwf.FDwfAnalogImpedanceStatus(hdwf, None)                       # Ignore last capture since we changed the frequency

            while True:
                if dwf.FDwfAnalogImpedanceStatus(hdwf, byref(sts)) == 0:
                    dwf.FDwfGetLastErrorMsg(szerr)
                    print(str(szerr.value))
                    quit()
                if sts.value == 2:
                    break

            dwf.FDwfAnalogImpedanceStatusMeasure(hdwf, DwfAnalogImpedanceImpedance, byref(impedance))   # Read the DUT impedance value
            dwf.FDwfAnalogImpedanceStatusMeasure(hdwf, DwfAnalogImpedanceImpedancePhase, byref(phase))  # Read the DUT phase value
            extfile.write(str(freq) + "\t" + str(abs(impedance.value)) + "\t" + str((phase.value / math.pi) * 180.0) + "\n")    # Write frequency, impedance and phase value to file

        extfile.close()

    dwf.FDwfAnalogImpedanceConfigure(hdwf, c_int(0))    # Measurement End

    final = time.time()                                 # Take time stamp
    infoOutput.insert(tk.INSERT, "Finished: " + str(round(final - initial, 2)) + "s\n")
    infoOutput.update()
    infoOutput.see("end")                               # Allows scrolling in text widget


def clearFunction():
    clearButton.update()
    infoOutput.delete("1.0", END)


def quitFunction():
    dwf.FDwfDeviceClose(hdwf)
    win.quit()


# endregion


# region Window Layout
# This is the section of code which creates the main window
w = 540  # width for the Tk root
h = 320  # height for the Tk root
ws = win.winfo_screenwidth()  # width of the screen
hs = win.winfo_screenheight()  # height of the screen
x = (ws / 2) - (w)
y = (hs / 2) - (h)
# set the dimensions of the screen and where it is placed
win.geometry("%dx%d+%d+%d" % (w, h, x, y))
win.configure(background="#F0F8FF")
win.title("Impedance Analyzer")


# This is the section of code which creates all labels
startFreqLabel = Label(win, text="Start Freq [Hz]", bg="#F0F8FF", font=("arial", 12, "normal"))
startFreqLabel.grid(row=1, column=1, sticky="W")

endFreqLabel = Label(win, text="End Freq [Hz]", bg="#F0F8FF", font=("arial", 12, "normal"))
endFreqLabel.grid(row=2, column=1, sticky="W")

deltaFreqLabel = Label(win, text="Delta Freq [Hz]", bg="#F0F8FF", font=("arial", 12, "normal"))
deltaFreqLabel.grid(row=3, column=1, sticky="W")

startAmpLabel = Label(win, text="Start Amp [V]", bg="#F0F8FF", font=("arial", 12, "normal"))
startAmpLabel.grid(row=4, column=1, sticky="W")

endAmpLabel = Label(win, text="End Amp [V]", bg="#F0F8FF", font=("arial", 12, "normal"))
endAmpLabel.grid(row=5, column=1, sticky="W")

deltaAmpLabel = Label(win, text="Delta Amp [V]", bg="#F0F8FF", font=("arial", 12, "normal"))
deltaAmpLabel.grid(row=6, column=1, sticky="W")

resistorLabel = Label(win, text="Resistor [Ohm]", bg="#F0F8FF", font=("arial", 12, "normal"))
resistorLabel.grid(row=7, column=1, sticky="W")

infoLabel = Label(win, text="Info", bg="#F0F8FF", font=("arial", 12, "normal"))
infoLabel.grid(row=8, column=1, sticky="W")


# This is the section of code which creates all text input boxes
startFreqInput = Entry(win)
startFreqInput.insert(END, str(freq_start))
startFreqInput.grid(row=1, column=2, padx=20, ipadx=20, sticky="W")

endFreqInput = Entry(win)
endFreqInput.insert(END, str(freq_end))
endFreqInput.grid(row=2, column=2, padx=20, ipadx=20)

deltaFreqInput = Entry(win)
deltaFreqInput.insert(END, str(freq_delta))
deltaFreqInput.grid(row=3, column=2, padx=20, ipadx=20)

startAmpInput = Entry(win)
startAmpInput.insert(END, str(amp_start))
startAmpInput.grid(row=4, column=2, padx=20, ipadx=20)

endAmpInput = Entry(win)
endAmpInput.insert(END, str(amp_end))
endAmpInput.grid(row=5, column=2, padx=20, ipadx=20)

deltaAmpInput = Entry(win)
deltaAmpInput.insert(END, str(amp_delta))
deltaAmpInput.grid(row=6, column=2, padx=20, ipadx=20)

resistanceInput = Entry(win)
resistanceInput.insert(END, str(resistance))
resistanceInput.grid(row=7, column=2, padx=20, ipadx=20)


# This is the section of code which creates all text output boxes
infoOutput = Text(win, height=5, width=25)
infoOutput.grid(row=8, column=2, sticky="W")


# This is the section of code which creates all buttons
connectButton = Button(
    win,
    text="Connect",
    state=NORMAL,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=connectFunction,)
connectButton.grid(row=1, column=3, padx=40, sticky="E", ipadx=25)

disconnectButton = Button(
    win,
    text="Disconnect",
    state=DISABLED,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=disconnectFunction,)
disconnectButton.grid(row=2, column=3, padx=40, sticky="E", ipadx=25)

setButton = Button(
    win,
    text="Set Parameters",
    state=DISABLED,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=setFunction,)
setButton.grid(row=4, column=3, padx=40, sticky="E", ipadx=25)

startButton = Button(
    win,
    text="Start",
    state=DISABLED,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=startFunction,)
startButton.grid(row=5, column=3, padx=40, sticky="E", ipadx=25)

clearButton = Button(
    win,
    text="Info Clear",
    state=NORMAL,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=clearFunction,)
clearButton.grid(row=6, column=3, padx=40, sticky="E", ipadx=25)

quitButton = Button(
    win,
    text="Quit",
    state=NORMAL,
    bg="#F0F8FF",
    font=("arial", 12, "normal"),
    command=quitFunction,)
quitButton.grid(row=7, column=3, padx=40, sticky="E", ipadx=25)
# endregion


# Runs the event loop of Tkinter
win.mainloop()
