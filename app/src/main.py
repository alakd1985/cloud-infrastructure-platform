
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str


app = FastAPI(
    title="Cloud Infrastructure Platform",
    description="Cloud-native infrastructure demonstration API",
    version="1.0.0",
)
items = []
next_item_id = 1

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {
        "application": "Cloud Infrastructure Platform",
        "version": "1.0.0",
        "description": "Cloud-native infrastructure platform"
    }

@app.post("/items", status_code=201)
def create_item(item: Item):
    global next_item_id

    new_item = {
        "id": next_item_id,
        "name": item.name,
        "description": item.description
    }

    items.append(new_item)
    next_item_id += 1

    return new_item

@app.get("/items")
def get_items():
    return items


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item

    raise HTTPException(
        status_code=404,
        detail="Item not found"
    )


@app.delete("/items/{item_id}")
def delele_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            items.remove(item)
            return {"message": "Item deleted successfully"}

    raise HTTPException(
        status_code=404,
        detail="Item not found"
    )


@app.put("/items/{item_id}")
def update_item(item_id: int, updated_item: Item):
    for item in items:
        if item["id"] == item_id:
            item["name"] = updated_item.name
            item["description"] = updated_item.description

        return item
    raise HTTPException(
        status_code=404,
        detail="Item not found"
    )


