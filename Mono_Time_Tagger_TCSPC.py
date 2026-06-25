# Direct setup TCSPC test for possible N2 Raman
# CH1 = function generator trigger
# CH4 = PMT signal
 
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
 
# ---------- Time Tagger driver path ----------
sys.path.append(r"C:\Program Files\Swabian Instruments\Time Tagger\driver\x64")
from TimeTagger import createTimeTagger, Correlation
 
# ================= SETTINGS =================
MONO_ADDRESS = "USB0::0x1FDE::0x0014::260B5176::INSTR"
 
REF_CH = 1
PMT_CH = 4
 
REF_TRIGGER_V = 0.50
PMT_TRIGGER_V = 0.30
 
# MONO_WAVELENGTH_NM = 248.0   # 248 nm excitation
MONO_WAVELENGTH_NM = 263.0   # possible N2 Raman region for 248 nm excitation
 
BIN_WIDTH_PS = 500           # 0.5 ns
N_BINS = 2000                # 1000 ns window
 
INTEGRATION_S = 1800         # 30 min
GRATING_NUMBER = 1
 
CSV_NAME = "Direct_TCSPC_263nm.csv"
PNG_NAME = "Direct_TCSPC_263nm.png"
# ============================================
 
mono = None
 
try:
    # ---------- connect mono ----------
    rm = pyvisa.ResourceManager()
    mono = rm.open_resource(MONO_ADDRESS)
    mono.timeout = 30000
 
    mono.write("handshake 0")
    mono.write("units nm")
 
    print("Mono ID:", mono.query("*IDN?").strip())
    print("Units:", mono.query("units?").strip())
 
    # ---------- select grating ----------
    mono.write(f"grating {GRATING_NUMBER}")
    mono.query("*OPC?")
    time.sleep(0.5)
    
    try:
        print("Current grating:", mono.query("grating?").strip())
    except:
        print("Grating query not available, but grating command was sent.")
 
    # ---------- open shutter ----------
    mono.write("shutter o")
    time.sleep(0.5)
 
    print(f"Move mono to {MONO_WAVELENGTH_NM:.1f} nm")
    mono.write(f"gowave {MONO_WAVELENGTH_NM:.3f}")
    mono.query("*OPC?")
    time.sleep(1.0)
 
    actual_wl = float(mono.query("wave?").strip())
    print(f"Actual wavelength = {actual_wl:.3f} nm")
 
    # ---------- connect to Time Tagger ----------
    tagger = createTimeTagger()
    tagger.setTriggerLevel(REF_CH, REF_TRIGGER_V)
    tagger.setTriggerLevel(PMT_CH, PMT_TRIGGER_V)
 
    hist = Correlation(
        tagger,
        REF_CH,
        PMT_CH,
        BIN_WIDTH_PS,
        N_BINS
    )
 
    print(f"Running TCSPC histogram for {INTEGRATION_S} s...")
    hist.startFor(int(INTEGRATION_S * 1e12), clear=True)
    hist.waitUntilFinished()
 
    counts = hist.getData()
    time_ns = hist.getIndex() / 1000.0
 
    # ---------- save ----------
    df = pd.DataFrame({
        "time_ns": time_ns,
        "counts": counts
    })
    df.to_csv(CSV_NAME, index=False)
 
    # ---------- plot ----------
    plt.figure(figsize=(8, 5))
    plt.plot(time_ns, counts)
    plt.xlabel("Time delay (ns)")
    plt.ylabel("Counts per bin")
    plt.title(f"Direct TCSPC Histogram at {actual_wl:.1f} nm")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PNG_NAME, dpi=300)
    plt.show()
 
    print("Done.")
    print("Saved:", CSV_NAME)
    print("Saved:", PNG_NAME)
 
finally:
    if mono is not None:
        try:
            mono.write("shutter c")
        except:
            pass
        mono.close()