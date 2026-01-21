from sqlalchemy import Column, Integer, String, Text, Boolean
from app.core.database import Base

class CMSPage(Base):
    __tablename__ = "cms_pages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    slug = Column(String(150), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    is_published = Column(Boolean, default=True)
