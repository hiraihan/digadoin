from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.modules.cms.models import CMSPage
from app.dependencies import require_editor, require_admin, get_current_user_optional
from app.modules.auth_user.models import User

router = APIRouter()

# =======================
# CREATE PAGE
# =======================
@router.post("/")
def create_page(
    title: str,
    slug: str,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)  # Require editor or admin
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
def get_pages(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Show all pages for now
    # In production, filter by is_published if user is not editor/admin
    return db.query(CMSPage).all()

# =======================
# GET PAGE BY SLUG
# =======================
@router.get("/{slug}")
def get_page(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    page = db.query(CMSPage).filter(CMSPage.slug == slug).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # If page is unpublished, only editor/admin can view
    if not page.is_published:
        if not current_user or current_user.role not in ["admin", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view unpublished pages"
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)  # Require editor or admin
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
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # Require admin only
):
    page = db.query(CMSPage).filter(CMSPage.id == page_id).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    db.delete(page)
    db.commit()
    return {"message": "Page deleted successfully"}
