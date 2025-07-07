from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata_obj = Base.metadata # Alembic will target this

class SampleTable(Base):
    __tablename__ = "sample_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

# You can add more models here and Alembic should pick them up
# as long as they use the same Base and metadata_obj is correctly targeted.
