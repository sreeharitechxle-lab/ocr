from pymongo import MongoClient
import pandas as pd
from io import BytesIO

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["business_card_db"]
collection = db["cards"]

# Check if there are any records
records = list(collection.find())
print(f"Number of records in database: {len(records)}")

if records:
    print("\nFirst record:")
    print(records[0])
    
    # Test DataFrame creation
    df = pd.DataFrame(records)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Test Excel export
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    
    print("\n✅ Excel export test successful!")
    print(f"Excel file size: {len(output.getvalue())} bytes")
else:
    print("\n⚠️ No records found in database")
