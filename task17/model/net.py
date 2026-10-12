"""KINGSMEAD-11: 33/11 kV primary substation and meshed 11 kV network. Single source of truth for solver, drawings and data sheet."""
# Cable types: R, X in ohm/km (90 C), continuous rating in A
CABLE = {"300": (0.130, 0.093, 465), "185": (0.211, 0.097, 360), "95": (0.411, 0.108, 245), "70": (0.568, 0.112, 205)}
# Source: 33 kV grid infeed, Thevenin behind impedance (ohm at 33 kV)
SRC_KV, SRC_Z = 33.6, complex(0.36, 3.60)
# Transformers: 33/11 kV, 15 MVA, Z 10 % on 15 MVA, X/R 20; HV taps 1..17, nominal 9, step 1.25 % (raising tap number adds HV turns, LV volts fall)
TX = {"T1": dict(S=15.0, z=0.10, xr=20.0), "T2": dict(S=15.0, z=0.10, xr=20.0)}
TAP_STEP, TAP_NOM, TAP_MIN, TAP_MAX = 0.0125, 9, 1, 17
AVC_TARGET_KV = 11.20          # AVC: tap giving section voltage closest to target
# Buses: 11 kV sections A, B; secondary substations S1..S12
# Routes: (route id, from, to, [(cable type, length m), ...]) -- sections in order from 'from' to 'to'
ROUTES = [
    ("F1-1", "A",  "S1",  [("300", 1150), ("185", 420)]),
    ("F1-2", "S1", "S2",  [("185", 860)]),
    ("F1-3", "S2", "S3",  [("185", 640), ("95", 380)]),
    ("F1-4", "S3", "S4",  [("95", 910)]),
    ("F2-1", "A",  "S5",  [("300", 980)]),
    ("F2-2", "S5", "S6",  [("185", 1240)]),
    ("F2-3", "S6", "S7",  [("95", 770), ("70", 450)]),
    ("F3-1", "B",  "S8",  [("300", 1320)]),
    ("F3-2", "S8", "S9",  [("185", 690), ("185", 510)]),
    ("F3-3", "S9", "S10", [("95", 880)]),
    ("F4-1", "B",  "S11", [("300", 760), ("185", 590)]),
    ("F4-2", "S11", "S12", [("95", 1060)]),
    ("IC-1", "S3", "S10", [("185", 1480)]),          # interconnector, normally closed (meshes F1 and F3)
    ("IC-2", "S6", "S11", [("185", 1630)]),          # second interconnector (meshes F2 and F4)
    ("NOP-1", "S4", "S8", [("95", 1210)]),           # normally open at S4 end
    ("NOP-2", "S7", "S12", [("95", 840)]),           # normally open at S12 end
]
# Loads at 09:00: kW, power factor (lagging)
LOAD = {"S1": (1450, 0.95), "S2": (980, 0.93), "S3": (1210, 0.94), "S4": (760, 0.92), "S5": (1630, 0.95), "S6": (1120, 0.90),
        "S7": (690, 0.91), "S8": (1380, 0.95), "S9": (1040, 0.93), "S10": (850, 0.92), "S11": (1720, 0.96), "S12": (910, 0.93)}
PV = dict(bus="S10", P_kW=4000.0, pf=0.95)       # absorbs reactive power at fixed pf (leading for the network)
CAP = dict(bus="S6", Q_kvar=1200.0)               # rated at 11.0 kV, Q scales with V^2
