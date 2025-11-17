from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from databases import Database
from typing import Optional, List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import os

Base = declarative_base()

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Fix Render's postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite specific settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

database = Database(DATABASE_URL)

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configure via ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


class TreeNode(Base):
    __tablename__ = 'tree_items'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    data = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('tree_items.id'), nullable=True)


# Drop and recreate tables (ONLY for development)
if ENVIRONMENT == "development":
    Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


class TreeItemCreate(BaseModel):
    name: str
    data: Optional[str] = None
    children: Optional[List['TreeItemCreate']] = None


class TreeItemUpdate(BaseModel):
    data: str


class TreeItemResponse(BaseModel):
    id: int
    name: str
    data: Optional[str] = None
    parent_id: Optional[int] = None
    children: Optional[List['TreeItemResponse']] = None


TreeItemCreate.model_rebuild()
TreeItemResponse.model_rebuild()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


async def insert_tree_recursive(item: TreeItemCreate, parent_id: Optional[int] = None) -> int:
    """Recursively insert tree nodes and return the root node id"""
    query = """
    INSERT INTO tree_items (name, data, parent_id)
    VALUES (:name, :data, :parent_id)
    """
    node_id = await database.execute(
        query,
        values={"name": item.name, "data": item.data, "parent_id": parent_id}
    )

    if item.children:
        for child in item.children:
            await insert_tree_recursive(child, parent_id=node_id)

    return node_id


async def build_tree_recursive(node_id: int) -> TreeItemResponse:
    """Recursively build tree structure from database"""
    query = "SELECT * FROM tree_items WHERE id = :node_id"
    node = await database.fetch_one(query, values={"node_id": node_id})

    if not node:
        return None

    children_query = "SELECT id FROM tree_items WHERE parent_id = :parent_id"
    children_ids = await database.fetch_all(children_query, values={"parent_id": node_id})

    children = []
    for child_row in children_ids:
        child = await build_tree_recursive(child_row['id'])
        if child:
            children.append(child)

    return TreeItemResponse(
        id=node['id'],
        name=node['name'],
        data=node['data'],
        parent_id=node['parent_id'],
        children=children if children else None
    )


@app.get("/api/tree")
async def retrieve_tree():
    """Get only root nodes and their nested children"""
    query = "SELECT id FROM tree_items WHERE parent_id IS NULL ORDER BY id"
    root_nodes = await database.fetch_all(query)

    if not root_nodes:
        return []

    trees = []
    for root in root_nodes:
        tree = await build_tree_recursive(root['id'])
        if tree:
            trees.append(tree)

    return trees


@app.get("/api/tree/all")
async def retrieve_all_items():
    """Get all items as a flat list (for debugging)"""
    query = "SELECT * FROM tree_items ORDER BY id"
    items = await database.fetch_all(query)
    return items


@app.post("/api/tree", response_model=dict)
async def create_tree_item(item: TreeItemCreate):
    """Replace the entire tree with new data"""
    # Delete all existing tree items
    delete_all_query = "DELETE FROM tree_items"
    await database.execute(delete_all_query)

    # Insert the new tree
    root_id = await insert_tree_recursive(item)
    return {"message": "Tree replaced successfully", "root_id": root_id}


@app.put("/api/tree/{item_id}/data")
async def update_tree_item_data(item_id: int, item: TreeItemUpdate):
    """Update only the data field of a specific tree item"""
    # Check if item exists
    check_query = "SELECT id FROM tree_items WHERE id = :item_id"
    existing = await database.fetch_one(check_query, values={"item_id": item_id})

    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    query = """
    UPDATE tree_items
    SET data = :data
    WHERE id = :item_id
    """
    await database.execute(query, values={"data": item.data, "item_id": item_id})
    return {"item_id": item_id, "data": item.data, "message": "Data updated successfully"}


@app.delete("/api/tree/{item_id}")
async def delete_tree_item(item_id: int):
    """Delete a tree item and all its children"""
    # Check if item exists
    check_query = "SELECT id FROM tree_items WHERE id = :item_id"
    existing = await database.fetch_one(check_query, values={"item_id": item_id})

    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    # Delete children recursively (SQLite doesn't support CASCADE with ForeignKey by default)
    async def delete_recursive(node_id: int):
        children_query = "SELECT id FROM tree_items WHERE parent_id = :parent_id"
        children = await database.fetch_all(children_query, values={"parent_id": node_id})

        for child in children:
            await delete_recursive(child['id'])

        delete_query = "DELETE FROM tree_items WHERE id = :item_id"
        await database.execute(delete_query, values={"item_id": node_id})

    await delete_recursive(item_id)
    return {"item_id": item_id, "message": "Item and children deleted successfully"}