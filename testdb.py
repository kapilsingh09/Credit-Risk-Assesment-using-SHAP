from database import prediction_collection

data = prediction_collection.find()

for document in data:
    print(document.get('default_probability',))

print("testdb runned")