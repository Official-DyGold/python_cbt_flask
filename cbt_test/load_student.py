import pandas as pd
from cbt_test.models import Student

excel_file = 'cbt_test/data.xlsx'

sheet_name = 'Sheet1'


try:
    df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit()

print("DataFrame Preview:")
print(df.head())
print(df.columns.tolist())


with app.app_context():
    try:
        for _, row in df.iterrows():
            student = Student(
                studentID=row['ID '],  # Replace with your column name
                fullname=row['Name'],    # Replace with your column name
                email=row['Email'],          # Replace with your column name
            )
            db.session.add(student)
        
        # Commit all changes to the database
        db.session.commit()
        print("Data successfully loaded into the Student table.")
    except Exception as e:
        db.session.rollback()
        print(f"Error writing to the database: {e}")