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
from fpdf import FPDF
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

cols=st.columns(3)
with cols[1]:
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

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'measurement_data' not in st.session_state:
    st.session_state.measurement_data = {}
if 'billing_info' not in st.session_state:
    st.session_state.billing_info = {}

def next_step():
    if st.session_state.step < 7:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 1:
        st.session_state.step -= 1


def generate_pdf(user_data):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'Billing and Measurement Receipt', ln=True, align='C')

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'User Information:', ln=True)

    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, f"Name: {user_data['name']}", ln=True)
    pdf.cell(200, 10, f"Email: {user_data['email']}", ln=True)
    pdf.cell(200, 10, f"Contact Number: {user_data['phone_number']}", ln=True)
    pdf.cell(200, 10, f"Order Date: {user_data['email']}", ln=True)
    pdf.cell(200, 10, f"Delivery Date: {user_data['email']}", ln=True)

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'Billing Information:', ln=True)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, "Address: 'Address'", ln=True)
    pdf.cell(200, 10, "Payment Method: 'Payment Method'", ln=True)
    # Create in-memory file
    pdf_output = io.BytesIO()
    pdf.output(pdf_output, 'S')
    pdf_output.seek(0)

    return pdf_output


# Function to generate PDF using reportlab
def generate_reportlab_pdf(user_data):
    buffer = io.BytesIO()
    # Create a PDF object
    p = canvas.Canvas(buffer, pagesize=letter)

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Billing and Measurement Receipt")

    # User Information
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 720, "User Information:")

    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Name: {user_data['name']}")
    p.drawString(100, 680, f"Email: {user_data['email']}")
    p.drawString(100, 660, f"Contact Number: {user_data['phone_number']}")
    p.drawString(100, 640, f"Order Date: {user_data['date']}")
    p.drawString(100, 620, f"Delivery Date: {user_data['delivery_date']}")

    # Billing Information
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 590, "Billing Information:")

    p.setFont("Helvetica", 12)
    p.drawString(100, 570, "Address: 'Address'")
    p.drawString(100, 550, "Payment Method: 'Payment Method'")

    # Save the PDF
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and return as bytes
    buffer.seek(0)
    return buffer.getvalue()


def main():

    maincols = st.columns([9,1])
    with maincols[1]:
        authenticator.logout('Logout')

    if st.session_state.step == 1:
        # Customer Information
        with maincols[0]:
            st.header("Customer Information")
        name = st.text_input("Name")
        phone_number = st.text_input("Phone Number")
        email = st.text_input("Email Address")
        date = st.date_input("Date", datetime.today())
        delivery_date = st.date_input("Delivery Date")
        st.session_state.measurement_data['name'] = name
        st.session_state.measurement_data['phone_number'] = phone_number
        st.session_state.measurement_data['email'] = email
        st.session_state.measurement_data['date'] = date
        st.session_state.measurement_data['delivery_date'] = delivery_date
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Next", on_click=next_step)
        

    elif st.session_state.step == 2:
        # Garment Type
        with maincols[0]:
            st.header("Garment Type")
        garment_type = st.radio("Please check the appropriate option", ["Suit", "Sherwani", "Blazer", "Other"])
        if garment_type == "Other":
            other_garment = st.text_input("Specify Other Garment Type")
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)
        with nexcols[1]:
            st.button("Next", on_click=next_step)

    elif st.session_state.step == 3:
        # Fabric Details
        with maincols[0]:
            st.header("Fabric Details")
        fabric_type = st.text_input("Fabric Type")
        fabric_color_pattern = st.text_input("Fabric Color/Pattern")
        lining_fabric = st.text_input("Lining Fabric")
        button_style_color = st.text_input("Button Style/Color")
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)
        with nexcols[1]:
            st.button("Next", on_click=next_step)

    elif st.session_state.step == 4:
        # Design Preferences
        with maincols[0]:
            st.header("Design Preferences")
        design_preferences = st.text_area("Any design preferences or custom requests?")
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)
        with nexcols[1]:
            st.button("Next", on_click=next_step)

    elif st.session_state.step == 5:
        # Body Measurements
        with maincols[0]:
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
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)
        with nexcols[1]:
            st.button("Next", on_click=next_step)

    elif st.session_state.step == 6:
        # Additional Notes/Instructions
        with maincols[0]:
            st.header("Additional Notes/Instructions")
        special_fit = st.text_area("Special Fit Preferences (e.g., loose around the arms, tapered waist, etc.)")
        reference_garments = st.text_area("Any Existing Garments for Reference")
        # padding = st.selectbox("Preferred Padding (light, medium, heavy for shoulders)", ["Light", "Medium", "Heavy"])
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)
        with nexcols[1]:
            st.button("Next", on_click=next_step)

    elif st.session_state.step == 7:
        # Billing Information
        with maincols[0]:
            st.header("Billing")
        total_bill = st.number_input("Total Bill Amount", min_value=0.0, step=0.01)
        advance_payment = st.number_input("Advance Payment", min_value=0.0, step=0.01)
        balance_payment = total_bill - advance_payment
        st.write(f"Balance Payment: {balance_payment}")
        # Navigation buttons
        nexcols = st.columns([1,1,8])
        with nexcols[0]:
            st.button("Back", on_click=prev_step)

        # Submit Button
        if st.button("Submit"):
            st.success("Form Submitted Successfully!")
            # Combine measurement and billing data
            user_data = st.session_state.measurement_data

            # Confirmation message and display of saved data
            st.write("Here is the summary of your details:")
            st.json(user_data)
            # pdf = generate_pdf(user_data)
            # st.write(pdf)
            # pdf_bytes = pdf.read()
            # st.write(pdf_bytes)
            # st.download_button(label="Download as PDF", data=pdf_bytes, file_name="user_details.pdf", mime="application/pdf")
            # Generate the PDF
            pdf_bytes = generate_reportlab_pdf(user_data)

            # Create a download button for the PDF
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="receipt.pdf",
                mime="application/pdf"
            )

            

## Login authentication
if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    with cols[1]:
        st.warning('Please enter your credentials')
elif authentication_status:
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    if __name__ == "__main__":
        main()
    # authenticator.logout('Logout', 'sidebar')
    st.sidebar.write("Welcome, {u} ".format(u=username))
    with st.container():
        st.sidebar.button("My Dashboard", use_container_width=True)
        st.sidebar.button("My Sales", use_container_width=True)
        st.sidebar.button("New Customer", use_container_width=True)
        st.sidebar.button("Search Customer", use_container_width=True)
    
