from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print(BASE_DIR)
# life span

ml_model={}
@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_model['model'] = joblib.load(os.path.join(BASE_DIR, 'credit_risk_model.pkl'))
    ml_model['threshold'] = joblib.load(os.path.join(BASE_DIR, 'best_threshold.pkl'))

    yield

    ml_model.clear()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#The only columns that user will see and provide inputs.
class LoanApplication(BaseModel): #Pydantic Model (Validation)
    person_age: int
    person_income: float
    person_home_ownership: str
    person_emp_length: float
    loan_intent: str
    loan_grade: str
    loan_amnt: float
    loan_int_rate: float
    loan_percent_income: float
    cb_person_default_on_file: str
    cb_person_cred_hist_length: int





@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post('/predict')
def predict(data : LoanApplication):
    input_df = pd.DataFrame([data.model_dump()])

    probability = float(ml_model['model'].predict_proba(input_df)[:, 1][0])
    threshold = float(ml_model["threshold"])

    prediction = int(probability >= threshold)

    return {
        "default_probability": probability,
        "default_prediction": prediction,
        "threshold": threshold,
        "Result": "High Risk" if prediction == 1 else "Low Risk"
    }

app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)