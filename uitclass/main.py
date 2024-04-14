# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from uitclass import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]




class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)


# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://localhost:8000", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/todos/", response_model=Todo)
def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)]):
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


@app.get("/todos/", response_model=list[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
        todos = session.exec(select(Todo)).all()
        return todos


@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo_by_id(todo: Todo, todo_id: int, session: Annotated[Session, Depends(get_session)]):
    todobyid = session.exec(select(Todo).where(Todo.id == todo_id))
    for item in todobyid:
        item.id = todo.id
        item.content = todo.content
        session.add(item)
        session.commit()
        #session.refresh(todobyid)
    return todo

@app.get("/todos/{todo_id}", response_model=list[Todo])
def read_todobyid(session: Annotated[Session, Depends(get_session)], todo_id: int):
        todobyid = session.exec(select(Todo).where(Todo.id == todo_id))
        return todobyid


@app.delete("/todos/{todo_id}", response_model=list[Todo])
def delete_todo(session: Annotated[Session, Depends(get_session)], todo_id: int):
    todofordel = session.exec(select(Todo).where(Todo.id == todo_id))
    for item in todofordel:
        session.delete(item)
    session.commit()
    todosafterdel = session.exec(select(Todo)).all()
    return todosafterdel
 