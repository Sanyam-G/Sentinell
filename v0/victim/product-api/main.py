from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock products data
PRODUCTS = [
    {
        "id": 1,
        "name": "Cloud Monitoring Pro",
        "price": 299.99,
        "description": "Enterprise-grade monitoring solution",
        "stock": 100
    },
    {
        "id": 2,
        "name": "Auto-Scaling Manager",
        "price": 499.99,
        "description": "Intelligent resource management",
        "stock": 50
    },
    {
        "id": 3,
        "name": "Alert Orchestrator",
        "price": 199.99,
        "description": "Smart alert routing and management",
        "stock": 75
    },
    {
        "id": 4,
        "name": "Chaos Engineering Suite",
        "price": 899.99,
        "description": "Test your system's resilience",
        "stock": 25
    }
]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-api"}

@app.get("/products")
async def get_products():
    logger.info("Fetching all products")
    return {"products": PRODUCTS, "count": len(PRODUCTS)}

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    logger.info(f"Fetching product {product_id}")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if product:
        return product
    return {"error": "Product not found"}, 404

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
