from src.utilities import utils

def test_find_match():
    dir = r"C:/Users/debru/Documents/Inspections/biosimilar/Evidence/031_PrimeVigilance Annual Performance review for the BE NCP (most recent one)"
    f = r"C:/Users/debru/Documents/Inspections/biosimilar/Evidence/031_PrimeVigilance Annual Performance review for the BE NCP (most recent one)/WVerlinden_Evaluation report 2023_Redacted.pdf"
    match = utils.find_match("vtd001 PSMF")
    print(match)


