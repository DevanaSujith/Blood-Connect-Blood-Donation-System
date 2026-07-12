from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["blood_connect"]

# Collections
donors_collection = db["donors"]
requests_collection = db["requests"]
hospitals_collection = db["hospitals"]
donations_collection = db["donations"]
donors_collection.create_index("phone", unique=True)
# ---------------- DONOR ----------------

def add_donor(data):
    try:
         data.pop("_id", None)   # ✅ REMOVE _id if exists
    # ✅ Normalize data
         data["phone"] = data["phone"].strip()
         data["name"] = data["name"].strip().title()
         data["city"] = data["city"].strip().lower()
         
         return donors_collection.insert_one(data)
    except:
         return None
         
def get_donors():
    donors = list(donors_collection.find())

    for donor in donors:
        last = donor.get("last_donation")

        if last:
            days = (datetime.now() - last).days
            if days >= 90:
                donor["eligibility"] = "Eligible"
            else:
                donor["eligibility"] = "Not Eligible"

    return donors

def search_donors(blood_group, location):
    return list(donors_collection.find({
        "blood": blood_group,
        "city": {"$regex": location, "$options": "i"},
        "availability": "Available",
        "verified": True 
    }))
def verify_donor(donor_id):
    return donors_collection.update_one(
        {"_id": donor_id},
        {"$set": {"verified": True}}
    )
def update_donation(donor_id, new_date):
    return donors_collection.update_one(
        {"_id": donor_id},
        {"$set": {
            "last_donation": new_date,
            "eligibility": "Not Eligible"
        }}
    )
def delete_donor(donor_id):
    return donors_collection.delete_one({"_id": donor_id})

# ---------------- REQUEST ----------------

def add_request(data):
    data["date"] = datetime.now()
    data["status"] = "Pending"
    return requests_collection.insert_one(data)

def get_requests():
    return list(requests_collection.find())

# ---------------- HOSPITAL ----------------

def add_hospital(data):
    return hospitals_collection.insert_one(data)

def get_hospitals():
    return list(hospitals_collection.find())

# ---------------- DONATION ----------------

def add_donation(data):
    data["date"] = datetime.now()
    return donations_collection.insert_one(data)

def get_donations():
    return list(donations_collection.find())

# ---------------- ELIGIBILITY CHECK ----------------

def check_eligibility(last_donation_date):
    if not last_donation_date:
        return True
    
    today = datetime.now()
    gap = (today - last_donation_date).days
    
    # Minimum 90 days gap
    return gap >= 90
