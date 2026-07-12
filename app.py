from dotenv import load_dotenv
import os

load_dotenv()
import streamlit as st
from datetime import date, datetime,timedelta
import os
import smtplib
from email.mime.text import MIMEText

# ---------------- EMAIL FUNCTION ----------------
def send_email(receiver_email, subject, message):
    sender_email = os.getenv("EMAIL")
    sender_password = os.getenv("PASSWORD")

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except:
        return False


from db import (
    add_donor, search_donors, get_donors,
    verify_donor, update_donation,
    add_request, add_hospital, add_donation,
    delete_donor
)

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Blood Connect", page_icon="🩸", layout="wide")

if not os.path.exists("certificates"):
    os.makedirs("certificates")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

menu = [
    "Home",
    "Donor Registration",
    "Search Donor",
    "Request Blood",
    "Donate Blood",
    "Hospital Registration",
    "Admin Login",
    "Admin Panel"
]

choice = st.sidebar.selectbox("Menu", menu)

# ---------------- HOME ----------------
if choice == "Home":
    st.title("🩸 Blood Connect")
    st.subheader("Connecting Donors with Patients")
    st.image("Bloodimage.jpg", width=900)
    st.success("Donate Blood • Save Lives ❤️")

# ---------------- DONOR REGISTRATION ----------------
elif choice == "Donor Registration":

    st.title("🩸 Donor Registration")

    name = st.text_input("Full Name")
    age = st.number_input("Age", 18, 65)
    weight = st.number_input("Weight (kg)", 50.0, 150.0)
    hb = st.number_input("Hemoglobin (g/dL)", 12.5, 20.0, step=0.1)

    blood_group = st.selectbox(
        "Blood Group",
        ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
    )

    phone = st.text_input("Phone Number")
    city = st.text_input("City")
    email = st.text_input("Email")
    last_donation = st.date_input("Last Donation Date")

    availability = st.selectbox("Availability", ["Available", "Not Available"])

    medical_certificate = st.file_uploader(
        "Upload Medical Certificate", type=["pdf", "jpg", "png"]
    )

    if st.button("Register"):

        if name == "" or phone == "" or city == "":
            st.error("Fill all fields")

        elif len(phone) != 10:
            st.error("Invalid phone number")

        else:
            today = date.today()
            days_since = (today - last_donation).days

            eligibility = "Eligible"

            if age < 18 or age > 65:
                eligibility = "Not Eligible"
            elif weight < 50:
                eligibility = "Not Eligible"
            elif hb < 12.5:
                eligibility = "Not Eligible"
            elif days_since < 90:
                eligibility = "Not Eligible"

            donor = {
                "name": name,
                "phone": phone,
                "email": email,
                "blood": blood_group,
                "city": city,
                "age": age,
                "weight": weight,
                "hb": hb,
                "availability": availability,
                "last_donation": datetime.combine(last_donation, datetime.min.time()),
                "eligibility": eligibility,
                "verified": False
            }
# Save certificate FIRST
            if medical_certificate:
              ext = medical_certificate.name.split(".")[-1]
              file_path = f"certificates/{name}_{phone}.{ext}"

              with open(file_path, "wb") as f:
               f.write(medical_certificate.getbuffer())

              donor["certificate"] = file_path  

# ✅ ONLY ONE TIME CALL
            result = add_donor(donor)

            if result:
              st.success("✅ Donor Registered Successfully")
            else:
              st.warning("⚠️ Donor already registered")

# ---------------- SEARCH DONOR ----------------
elif choice == "Search Donor":

    st.title("🔍 Search Blood Donor")

    blood_group = st.selectbox(
        "Blood Group",
        ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
    )
    city = st.text_input("City")
    if st.button("Search"):

        results = search_donors(blood_group, city)

        if not results:
            st.error("❌ No matching donor found")

        for donor in results:
            if donor.get("availability") == "Available":

                st.success("✅ Donor Found")
                st.write("Name:", donor.get("name"))
                st.write("Blood:", donor.get("blood"))
                st.write("Phone:", donor.get("phone"))
                st.write("City:", donor.get("city"))
                st.write("---")

# ---------------- REQUEST BLOOD (EMAIL ONLY) ----------------
elif choice == "Request Blood":

    st.title("🩸 Blood Request")

    blood = st.selectbox(
        "Blood Group",
        ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
    )
    city = st.text_input("City")

    if st.button("Send Request"):

        add_request({"blood": blood, "city": city})

        donors = get_donors()
        notified = False

        for donor in donors:

          if (
        donor.get("blood") == blood and
        donor.get("availability") == "Available" and
        donor.get("city", "").lower() == city.lower()
          ):

                email = donor.get("email")
                admin_phone = "9876543210"  

                message = f"""
                URGENT BLOOD REQUEST 🚨

                Blood Group: {blood}
                Location: {city}

                Please contact immediately:
                📞 Admin: {admin_phone}

                Your help can save a life ❤️
                """

                if email:
                    success = send_email(
                        email,
                        "URGENT Blood Needed",
                        message
                    )

                    if success:
                        st.success(f"📧 Email sent to {donor.get('name')}")
                    else:
                        st.error(f"❌ Email failed for {donor.get('name')}")

                notified = True

        if not notified:
            st.warning("⚠️ No matching donors available")

# ---------------- DONATE BLOOD ----------------
elif choice == "Donate Blood":

    st.title("🩸 Donate Blood")
    st.info("Enter your registered phone number to update donation")
    phone = st.text_input("Enter Your Phone Number")
    donation_date = st.date_input("Date")

    if st.button("Donate"):

        donor_found = None

        for d in get_donors():
            if d.get("phone") == phone:
                donor_found = d
                break

        if not donor_found:
            st.error("❌ Donor not found")

        else:
            last = donor_found.get("last_donation")

            if last:
                last = last.date()
                st.info(f"Your last donation was on {last}")
                days = (date.today() - last).days
            else:
                days = 999

            if days < 90:
                next_date = last + timedelta(days=90)
                st.info(f"You can donate again after {next_date}")
            else:
                update_donation(
                    donor_found.get("_id"),
                    datetime.combine(donation_date, datetime.min.time())
                )

                add_donation({
                    "donor_id": donor_found.get("_id"),
                    "name": donor_found.get("name")
                })

                st.success("✅ Donation recorded")

# ---------------- HOSPITAL REGISTRATION ----------------
elif choice == "Hospital Registration":

    st.title("🏥 Hospital Registration")

    name = st.text_input("Hospital Name")
    location = st.text_input("Location")
    phone = st.text_input("Phone")
    email = st.text_input("Email")

    if st.button("Register"):

        if name and location and phone and email:

            add_hospital({
                "name": name,
                "location": location,
                "phone": phone,
                "email": email,
                "verified": False
            })

            st.success("✅ Hospital Registered")
        else:
            st.error("❌ Fill all fields")

# ---------------- ADMIN LOGIN ----------------
elif choice == "Admin Login":

    st.title("🔐 Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "admin" and password == "1234":
            st.session_state.is_admin = True
            st.success("✅ Login Successful")
        else:
            st.error("❌ Invalid Credentials")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":

    if not st.session_state.is_admin:
        st.error("⛔ Access Denied! Please login")
    else:
        st.title("🛠 Admin Panel")

        donors = get_donors()

        for i, donor in enumerate(donors):

             st.write("-----")
             st.write("Name:", donor.get("name"))
             st.write("Blood:", donor.get("blood"))
             st.write("City:", donor.get("city"))
             st.write("Eligibility:", donor.get("eligibility"))
             if st.button(f"🗑 Delete {donor.get('name')}", key=f"delete_{i}"):
                delete_donor(donor.get("_id"))
                st.success("❌ Donor deleted")
                st.rerun()
                st.divider()

             file_path = donor.get("certificate")

             if file_path and os.path.exists(file_path):
                 with open(file_path, "rb") as f:
                     file_bytes = f.read()

                 st.download_button(
                    "📄 View Certificate",
                    data=file_bytes,
                    file_name=os.path.basename(file_path),
                    mime="application/octet-stream",
                    key=f"cert_{i}"
                 )

                 if file_path.lower().endswith(("jpg", "png", "jpeg")):
                     st.image(file_path, width=200)

             else:
               st.info("⚠️ No certificate uploaded")

    # ✅ THIS SHOULD BE OUTSIDE ELSE
             if not donor.get("verified", False):
                 if st.button(f"Verify {donor.get('name')}", key=f"verify_{i}"):
                     verify_donor(donor.get("_id"))
                     st.success("✅ Verified")
             else:
                 st.success("Already Verified")