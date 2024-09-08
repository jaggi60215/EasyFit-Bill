import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import re
from twilio.rest import Client
import random
import string
import sqlite3
import streamlit_authenticator as stauth

st.set_page_config(page_title="EasyFit Bill", page_icon=":dress:", layout="wide")

names = ["Akshay", "Umesh", "Pratik"]
usernames = ["akshay", "umesh", "pratik"]
passwords = ["Akshay12", "Umesh12", "Pratik12"]

hashed_passwords = stauth.utilities.hasher.Hasher(passwords).generate()

common_conn = sqlite3.connect("creds.db")
common_cursor = common_conn.cursor()

cmd = "CREATE TABLE IF NOT EXISTS credentials (names TEXT, usernames TEXT, passwords TEXT)"
common_cursor.execute(cmd)

def get_creds():
    common_cursor.execute("select * from credentials")
    res = common_cursor.fetchall()
    credf = pd.DataFrame(res, columns=["names", "usernames", "pwds"])
    return credf

credf = get_creds()

for i,j in enumerate(usernames):
    if j not in list(credf["usernames"]):
        common_cursor.execute('INSERT INTO credentials VALUES("{name}","{uname}","{hash_pwd}")'.format(name=names[i],uname=usernames[i],hash_pwd=hashed_passwords[i]))
        common_conn.commit()

credf = get_creds()

names = list(credf["names"])
usernames = list(credf["usernames"])
passwords = list(credf["pwds"])

temp_dict = {}
for k,i in enumerate(usernames):
    temp_dict[i] = {"email": "", "name": names[k], "password": passwords[k]}

credentials = {}
credentials["usernames"] = temp_dict

# App Title
st.title("Tailor Measurement Form")

authenticator = stauth.Authenticate(credentials, "EasyFit Bill", "abc123", cookie_expiry_days=30.0)
name, authentication_status, username = authenticator.login("main")

# Function to generate OTP
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# Function to send OTP via SMS
def send_otp_via_sms(phone_number, otp):
    # Twilio credentials
    account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
    auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
    twilio_phone_number = 'YOUR_TWILIO_PHONE_NUMBER'
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'Your OTP for credential reset: {otp}',
        from_=twilio_phone_number,
        to=phone_number
    )

    return message.sid

def main():

    # Customer Information
    st.header("Customer Information")
    name = st.text_input("Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email Address")
    date = st.date_input("Date", datetime.today())
    delivery_date = st.date_input("Delivery Date")

    # Garment Type
    st.header("Garment Type")
    garment_type = st.radio("Please check the appropriate option", ["Suit", "Sherwani", "Blazer", "Other"])
    if garment_type == "Other":
        other_garment = st.text_input("Specify Other Garment Type")

    # Fabric Details
    st.header("Fabric Details")
    fabric_type = st.text_input("Fabric Type")
    fabric_color_pattern = st.text_input("Fabric Color/Pattern")
    lining_fabric = st.text_input("Lining Fabric")
    button_style_color = st.text_input("Button Style/Color")

    # Design Preferences
    st.header("Design Preferences")
    design_preferences = st.text_area("Any design preferences or custom requests?")

    # Body Measurements
    st.header("Body Measurements")

    measurement_metric = st.radio("Please check the appropriate option", ["Inches", "Centimeter"])
    def get_measurement(label):
        return st.number_input(f"{label} (in {measurement_metric})", min_value=0.0, step=0.1)

    chest = get_measurement("Chest")
    waist = get_measurement("Waist")
    hips = get_measurement("Hips")
    shoulders = get_measurement("Shoulders")
    neck = get_measurement("Neck")

    st.subheader("Arm Length")
    right_arm = get_measurement("Right Arm")
    left_arm = get_measurement("Left Arm")

    sleeve_length = get_measurement("Sleeve Length")
    bicep = get_measurement("Bicep")
    wrist = get_measurement("Wrist")
    jacket_length = get_measurement("Jacket Length")
    back_length = get_measurement("Back Length")

    st.subheader("Trouser Measurements (if applicable)")
    trouser_waist = get_measurement("Trouser Waist")
    trouser_inseam = get_measurement("Trouser Inseam")
    thigh_circumference = get_measurement("Thigh Circumference")
    knee_circumference = get_measurement("Knee Circumference")
    ankle_circumference = get_measurement("Ankle Circumference")

    height = get_measurement("Height")
    weight = get_measurement("Weight (in kg or lbs)")

    # Additional Notes/Instructions
    st.header("Additional Notes/Instructions")
    special_fit = st.text_area("Special Fit Preferences (e.g., loose around the arms, tapered waist, etc.)")
    reference_garments = st.text_area("Any Existing Garments for Reference")
    # padding = st.selectbox("Preferred Padding (light, medium, heavy for shoulders)", ["Light", "Medium", "Heavy"])

    # Billing Information
    st.header("Billing")
    total_bill = st.number_input("Total Bill Amount", min_value=0.0, step=0.01)
    advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01)
    balance_payment = total_bill - advance_payment
    st.write(f"Balance Payment: {balance_payment}")

    # Submit Button
    if st.button("Submit"):
        st.success("Form Submitted Successfully!")
        # You can process or save the form data here

## Login authentication
if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your credentials')
elif authentication_status:
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    if __name__ == "__main__":
        main()
    authenticator.logout('Logout', 'sidebar')
