from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.cms.models import CMSPage

router = APIRouter()

# =======================
# CREATE PAGE
# =======================
@router.post("/")
def create_page(
    title: str,
    slug: str,
    content: str,
    db: Session = Depends(get_db)
):
    existing = db.query(CMSPage).filter(CMSPage.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )

    page = CMSPage(
        title=title,
        slug=slug,
        content=content
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page

# =======================
# GET ALL PAGES
# =======================
@router.get("/")
def get_pages(db: Session = Depends(get_db)):
    return db.query(CMSPage).all()

# =======================
# GET PAGE BY SLUG
# =======================
@router.get("/{slug}")
def get_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(CMSPage).filter(CMSPage.slug == slug).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    return page

# =======================
# UPDATE PAGE
# =======================
@router.put("/{page_id}")
def update_page(
    page_id: int,
    title: str,
    content: str,
    is_published: bool,
    db: Session = Depends(get_db)
):
    page = db.query(CMSPage).filter(CMSPage.id == page_id).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    page.title = title
    page.content = content
    page.is_published = is_published

    db.commit()
    db.refresh(page)
    return page

# =======================
# DELETE PAGE
# =======================
@router.delete("/{page_id}")
def delete_page(page_id: int, db: Session = Depends(get_db)):
    page = db.query(CMSPage).filter(CMSPage.id == page_id).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    db.delete(page)
    db.commit()
    return {"message": "Page deleted successfully"}
