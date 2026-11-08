import time
from typing import Optional, Union
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from .database import Base, engine, get_db
from .models import Product

app = FastAPI(title="FastAPI + MySQL CRUD", version="2.0.0")


class ProductSchema(BaseModel):
    name: str
    price: Union[str, float, int]


@app.on_event("startup")
def startup_db_client():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            retries -= 1
            time.sleep(3)


# READ ALL - Listar todos los productos
@app.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()


# READ ONE - Obtener un producto por ID
@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


# CREATE - Crear un producto (soporta JSON body o Query params)
@app.post("/api/products", status_code=201)
def create_product(
    name: Optional[str] = Query(default=None, description="Nombre del producto"),
    price: Optional[str] = Query(default=None, description="Precio del producto"),
    payload: Optional[ProductSchema] = Body(default=None),
    db: Session = Depends(get_db)
):
    final_name = name if name is not None else (payload.name if payload else None)
    final_price = price if price is not None else (str(payload.price) if payload else None)

    if not final_name or final_price is None:
        raise HTTPException(status_code=400, detail="Se requiere el nombre y el precio del producto")

    product = Product(name=final_name.strip(), price=str(final_price).strip())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# UPDATE - Actualizar un producto existente por ID (soporta JSON body o Query params)
@app.put("/api/products/{product_id}")
def update_product(
    product_id: int,
    name: Optional[str] = Query(default=None, description="Nuevo nombre del producto"),
    price: Optional[str] = Query(default=None, description="Nuevo precio del producto"),
    payload: Optional[ProductSchema] = Body(default=None),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    final_name = name if name is not None else (payload.name if payload else None)
    final_price = price if price is not None else (str(payload.price) if payload else None)

    if not final_name or final_price is None:
        raise HTTPException(status_code=400, detail="Se requiere el nombre y el precio para actualizar")

    product.name = final_name.strip()
    product.price = str(final_price).strip()
    db.commit()
    db.refresh(product)
    return product


# DELETE - Eliminar un producto por ID
@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(product)
    db.commit()
    return {"message": "Producto eliminado correctamente", "id": product_id}
