import ssl

import json

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def getMessage(phoneNumber):
    print(f"getting loan request data for {phoneNumber}")
    partReleaseAmt = find_Pr_amt(phoneNumber)
    return partReleaseAmt

def find_Pr_amt(phone_number):
    # Connect to the MongoDB instance
    print(f"getting part release data for cx with phone: {phone_number}")
    with open("mohit_details.json", 'r') as file:
        data = json.load(file)

    for item in data['typeSchema']:
        if phone_number in item['phones']:
            return item['partReleaseAmountWithoutRebate']

    return None  # Return None if the phone number is not found in any object
