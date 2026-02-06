from extraction import extract_business_card_details

# Sample 1: Based on user provided image thumbnail
# "Communications Manager"
# "+91 1234567890"
# "sundarkumar@gmail.com"
# "Lyero & Company Real Estate"
# "Lucknow Indranagar"

sample_text_1 = """
Communications Manager
+91 1234567890
sundarkumar@gmail.com
Logo
Lyero & Company
Real Estate
Lucknow Indranagar
"""

# Sample 2: Generic
sample_text_2 = """
John Doe
Software Engineer
Tech Solutions Inc.
123 Tech Park, Silicon Valley, CA 94000
john.doe@techsolutions.com
(555) 123-4567
www.techsolutions.com
"""

# Sample 3: Harder case
sample_text_3 = """
Jane Smith
Director of Marketing
Global Corp
jane@global.com
+1 415 555 0199
"""

def print_result(name, text, f):
    f.write(f"\n--- {name} ---\n")
    details = extract_business_card_details(text)
    for k, v in details.items():
        f.write(f"{k}: {v}\n")

if __name__ == "__main__":
    with open("extraction_results.txt", "w") as f:
        print_result("Test 1 (User thumbnail approx)", sample_text_1, f)
        print_result("Test 2 (Standard)", sample_text_2, f)
        print_result("Test 3 (Minimal)", sample_text_3, f)
