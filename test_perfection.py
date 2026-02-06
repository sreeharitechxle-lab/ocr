import json
from extraction import extract_business_card_details

text = """
N.V. SELVAKUMAR AC mL
Sales Head (South & West)
ASSAM CARBON PRODUCTS LTD
Assam Carbon Products Ltd
2. IDA, Phase-I, Patancheru,
Sangareddy (Dist.),
Telangana State - 502319
9488473006
(08455) 242087 / 89
sales.head.sw@ascarbon.com
www.assamcarbon.in
"""

def test():
    # We can't easily see internal state unless we modify it or return it.
    # For now, let's just run it and see the output carefully.
    res = extract_business_card_details(text)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    test()
