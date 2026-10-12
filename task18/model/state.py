"""Night-shift / site log applied to the drawn (design) frame: state at Day 12, 07:00."""
import copy, frame as F, fem

def final(**over):
    beam = copy.deepcopy(F.BEAM)
    beam[("L2", "3-4")] = ("457x191x74 UB", "M", "S")      # Day 7: end plate at grid 4 not bolted -> simple until completed
    plant = dict(F.PLANT); plant["a"] = F.PLANT_TEMP_A        # Day 9: AHU-2 at temporary landing position, move scheduled Day 15
    kw = dict(BEAM=beam, PLANT=plant, BRACE=[F.BRACE[0]])     # Day 4: BR2 disconnected for duct route, reinstate Day 14
    kw.update(over)
    return fem.config(**kw)
