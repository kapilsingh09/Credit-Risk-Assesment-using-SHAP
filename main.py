import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from database import prediction_collection

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ml_model = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_model["model"] = joblib.load(os.path.join(BASE_DIR, "credit_risk_model.pkl"))
    ml_model["threshold"] = joblib.load(os.path.join(BASE_DIR, "best_threshold.pkl"))
    yield
    ml_model.clear()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoanApplication(BaseModel):
    person_age: int = Field(ge=18, le=100)
    person_income: float = Field(gt=0)
    person_home_ownership: Literal["RENT", "OWN", "MORTGAGE", "OTHER"]
    person_emp_length: float = Field(ge=0)
    loan_intent: Literal[
        "PERSONAL", "EDUCATION", "MEDICAL",
        "VENTURE", "HOMEIMPROVEMENT", "DEBTCONSOLIDATION",
    ]
    loan_grade: Literal["A", "B", "C", "D", "E", "F", "G"]
    loan_amnt: float = Field(gt=0)
    loan_int_rate: float = Field(ge=0)
    loan_percent_income: float = Field(ge=0)
    cb_person_default_on_file: Literal["Y", "N"]
    cb_person_cred_hist_length: int = Field(ge=0)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(data: LoanApplication):
    input_data = data.model_dump()
    input_df = pd.DataFrame([input_data])

    probability = float(ml_model["model"].predict_proba(input_df)[:, 1][0])
    threshold = float(ml_model["threshold"])
    prediction = int(probability >= threshold)

    result = {
        "default_probability": probability,
        "default_prediction": prediction,
        "threshold": threshold,
        "Result": "High Risk" if prediction == 1 else "Low Risk",
    }

    try:
        prediction_collection.insert_one({
            **result,
            "input": input_data,
            "created_at": datetime.now(timezone.utc),
        })
    except PyMongoError:
        logger.exception("Prediction save nahi hui")

    return result

@app.get('/predict-history')
def predict_histroy():
    predictions  = prediction_collection.find().sort('created_at',-1).limit(10)
    return [
          {
            "prediction": prediction.get("default_prediction", "unknown"),
            "probability": prediction.get("default_probability", "unknown"),
            "result": prediction.get("Result", "unknown"),
            "input": prediction.get("input", "unknown"),
            "created_at": prediction.get("created_at", "unknown")
        }
            for prediction in predictions
        
    ]

app.mount(
    "/",
    StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True),
    name="static",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, host="127.0.0.1", port=8000)