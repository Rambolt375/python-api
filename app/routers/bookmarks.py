import uuid
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserDB, BookmarkDB
from app.schemas import BookmarkPATCH, BookmarkPOST
from app.dependencies import get_current_user, require_verification

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_bookmark(bookmark: BookmarkPOST, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    new_bookmark = BookmarkDB(
        owner_id = current_user.id,
        title = bookmark.title,
        url = str(bookmark.url),
        tag = bookmark.tag.lower()
    )
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    return new_bookmark

@router.get("", status_code=status.HTTP_200_OK)
def get_bookmark(tag: str | None = None, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(BookmarkDB).filter(BookmarkDB.owner_id == current_user.id)
    if tag:
        query = query.filter(BookmarkDB.tag == tag.lower())
    return query.all()

@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_bookmark_by_id(id: uuid.UUID, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    db_bookmark = db.query(BookmarkDB).filter(BookmarkDB.owner_id == current_user.id, BookmarkDB.id == id).first()

    if not db_bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return db_bookmark

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(id: uuid.UUID, current_user: UserDB = Depends(require_verification), db: Session = Depends(get_db)):
    db_bookmark = db.query(BookmarkDB).filter(BookmarkDB.owner_id == current_user.id, BookmarkDB.id == id).first()

    if not db_bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book of ID {id} is not exists")

    db.delete(db_bookmark)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{id}", status_code=status.HTTP_200_OK)
def update_bookmark(id: uuid.UUID, bookmark: BookmarkPATCH, current_user: UserDB = Depends(require_verification), db: Session = Depends(get_db)):
    db_bookmark = db.query(BookmarkDB).filter(BookmarkDB.owner_id == current_user.id, BookmarkDB.id == id).first()

    if not db_bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bookmark {id} not found")

    update_payload = bookmark.model_dump(exclude_unset=True)
    if "tag" in update_payload and update_payload["tag"]:
        update_payload["tag"] = update_payload["tag"].lower()
    if "url" in update_payload and update_payload["url"]:
        update_payload["url"] = str(update_payload["url"])

    for key, value in update_payload.items():
        setattr(db_bookmark, key, value)

    db.commit()
    db.refresh(db_bookmark)
    return db_bookmark