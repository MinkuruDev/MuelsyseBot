import pyotp
# import qrcode

import global_vars

# 1. Generate a random Base32 secret
# secret = pyotp.random_base32()
secret = global_vars.TOTP_SECRET
# print("Secret:", secret)

# 2. Create a TOTP object (30s interval, 6 digits by default)
muelsyse_bot_totp = pyotp.TOTP(secret)

# 3. Generate otpauth:// URI for QR code
# "MuelsyseBot" = issuer, "Admin" = account name
# uri = muelsyse_bot_totp.provisioning_uri(name="Admin", issuer_name="MuelsyseBot")
# print("URI:", uri)

# 4. Generate and save QR code
# img = qrcode.make(uri)
# img.save("totp-qr.png")
# print("QR code saved as totp-qr.png")

def validate_totp(user_input):
    return muelsyse_bot_totp.verify(user_input)

if __name__ == "__main__":
    # Example usage
    while True:
        user_code = input("Enter the 6-digit code from your authenticator app: ")
        if validate_totp(user_code):
            print("Code is valid!")
        else:
            print("Invalid code.")