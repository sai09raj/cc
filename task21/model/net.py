"""TR-21: Hartsdown Tramway 750 V DC traction supply. Single source of truth for solver, drawing and data sheet."""
# section conductor types: (description, loop resistance ohm/km = contact line + feeder in parallel, plus return rail)
COND = {"K1": ("contact wire 107 mm2 Cu + 2 x 240 mm2 Al feeder; twin 54E1 rail", 0.027),
        "K2": ("contact wire 107 mm2 Cu + 240 mm2 Al feeder; 54E1 rail", 0.037),
        "K3": ("contact wire 107 mm2 Cu, no feeder; 59R2 grooved rail", 0.050),
        "K4": ("contact wire 80 mm2 Cu, no feeder; 59R2 grooved rail", 0.065),
        "K5": ("contact wire 150 mm2 Cu + 2 x 400 mm2 Al feeder; twin 54E1 rail", 0.019)}
# traction substations: node, no-load voltage E (V) at normal tap, internal resistance (ohm, rectifier + cables)
TSS = {"TSS-A": ("A", 835.0, 0.021), "TSS-B": ("B", 835.0, 0.024), "TSS-C": ("C", 835.0, 0.019), "TSS-D": ("D", 835.0, 0.022)}
TAP = {-1: -15.0, 0: 0.0, 1: 15.0}     # rectifier transformer tap: change of no-load voltage (V)
V_MIN = 600.0                          # minimum pantograph voltage for the peak check (V)
# routes: (id, from node, to node, [(conductor, length m), ...]) in drawing order
ROUTES = [
    ("L1", "A", "N1", [("K5", 620), ("K1", 540)]),
    ("L2", "N1", "N2", [("K1", 480), ("K2", 560)]),
    ("L3", "N2", "N3", [("K2", 520), ("K2", 410)]),
    ("L4", "N3", "B", [("K1", 450), ("K5", 380)]),
    ("M1", "N2", "N4", [("K2", 430), ("K3", 360)]),
    ("M2", "N4", "C", [("K3", 470), ("K1", 300)]),
    ("M3", "C", "N3", [("K1", 390), ("K3", 500)]),
    ("S1", "N1", "N5", [("K2", 400), ("K3", 520)]),
    ("S2", "N5", "N6", [("K3", 440), ("K3", 350)]),
    ("S3", "N2", "N6", [("K2", 380), ("K3", 470)]),
    ("S4", "N6", "N7", [("K3", 580), ("K2", 420)]),
    ("S5", "N7", "D", [("K2", 330), ("K5", 410)]),
    ("S6", "N3", "N7", [("K2", 450), ("K2", 440)]),
    ("S7", "N6", "N8", [("K4", 480), ("K4", 390)]),
    ("N9R", "N4", "N9", [("K3", 520), ("K4", 410)]),
    ("X1", "N9", "N1", [("K4", 520), ("K3", 450)]),
]
# trams at stops in the 07:30 SCADA snapshot: id -> (node, power kW drawn at the pantograph)
TRAMS = {"T104": ("N1", 760.0), "T117": ("N3", 980.0), "T122": ("N4", 620.0), "T109": ("N5", 840.0),
         "T131": ("N7", 1150.0), "T126": ("N8", 820.0), "T113": ("N9", 890.0), "T140": ("B", 560.0)}
