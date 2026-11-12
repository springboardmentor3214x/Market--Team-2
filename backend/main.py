from fastapi import FastAPI

app = FastAPI(title="Market Research API")

@app.get("/health")
def health():
    return {"status": "ok"}
    