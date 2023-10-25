import csv
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL':'https://facerecognition-41dc8-default-rtdb.asia-southeast1.firebasedatabase.app/'})

# Reference to the Realtime Database
ref = db.reference('Students')

# Fetch data
data = ref.get()

# Create and write to a CSV file
csv_file_name = "Students.csv"

with open(csv_file_name, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write the header row with column names
    if data:
        header = data[list(data.keys())[0]].keys()
        csv_writer.writerow(header)
    
    # Write data rows
    for key, value in data.items():
        csv_writer.writerow(value.values())
    
print(f'Data exported to {csv_file_name}')
