from database import engine, get_db
import models
models.Base.metadata.create_all(bind=engine)
print("Database connected")
