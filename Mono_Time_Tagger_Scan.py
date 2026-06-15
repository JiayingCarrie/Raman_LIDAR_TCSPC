# LED spectrum scan: CS260B + Time Tagger Ultra
# Plot: photon counts/s vs wavelength
 
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvisa
 
# ---------- Time Tagger driver path ----------
sys.path.append(r"C:\Program Files\Swabian Instruments\Time Tagger\driver\x64")
from TimeTagger import createTimeTagger, Countrate
 
# ================= SETTINGS =================
MONO_ADDRESS = "USB0::0x1FDE::0x0014::260B5176::INSTR"
 
PMT_CH = 4
TRIGGER_LEVEL_V = 0.30
 
START_NM = 230
END_NM = 400
STEP_NM = 5
 
INTEGRATION_S = 2.0
SETTLE_S = 0.5
 
GRATING_NUMBER = 1
 
CSV_NAME = "LED_spectrum_230_400nm.csv"
PNG_NAME = "LED_spectrum_230_400nm.png"
# ============================================
 
mono = None
 
try:
    # ---------- connect to CS260B ----------
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
 
    # ---------- connect to Time Tagger ----------
    tagger = createTimeTagger()
    tagger.setTriggerLevel(PMT_CH, TRIGGER_LEVEL_V)
 
    rate = Countrate(tagger, [PMT_CH])
 
    # ---------- scan ----------
    results = []
    wavelengths = np.arange(START_NM, END_NM + STEP_NM, STEP_NM)
 
    for wl in wavelengths:
        print(f"\nMoving to {wl:.1f} nm")
 
        mono.write(f"gowave {wl:.3f}")
        mono.query("*OPC?")
        time.sleep(SETTLE_S)
 
        actual_wl = float(mono.query("wave?").strip())
 
        rate.startFor(int(INTEGRATION_S * 1e12), clear=True)
        rate.waitUntilFinished()
 
        cps = float(rate.getData()[0])
 
        print(f"{actual_wl:.3f} nm -> {cps:.1f} counts/s")
 
        results.append({
            "wavelength_nm": actual_wl,
            "photon_counts_per_s": cps
        })
 
    # ---------- save ----------
    df = pd.DataFrame(results)
    df.to_csv(CSV_NAME, index=False)
 
    # ---------- plot ----------
    plt.figure(figsize=(8, 5))
    plt.plot(df["wavelength_nm"], df["photon_counts_per_s"], marker="o")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Photon counts/s")
    plt.title("LED Spectrum")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PNG_NAME, dpi=300)
    plt.show()
 
    print("\nDone.")
    print("Saved CSV:", CSV_NAME)
    print("Saved plot:", PNG_NAME)
 
finally:
    if mono is not None:
        try:
            mono.write("shutter c")
        except:
            pass
        mono.close()