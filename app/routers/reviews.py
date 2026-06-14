"""
Product reviews router — star ratings and customer feedback.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ProductReview, Product, UserRole
from app.auth import get_current_user
from app.schemas import ReviewCreate, ReviewResponse, ProductRatingSummary

router = APIRouter(prefix="/reviews", tags=["Product Reviews"])


@router.get("/product/{product_id}", response_model=List[ReviewResponse])
async def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all reviews for a specific product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = (
        db.query(ProductReview)
        .filter(ProductReview.product_id == product_id)
        .order_by(ProductReview.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for r in reviews:
        result.append(ReviewResponse(
            id=r.id,
            product_id=r.product_id,
            user_id=r.user_id,
            rating=r.rating,
            comment=r.comment,
            reviewer_name=r.user.full_name or r.user.username,
            created_at=r.created_at,
            updated_at=r.updated_at,
        ))
    return result


@router.get("/product/{product_id}/summary", response_model=ProductRatingSummary)
async def get_product_rating_summary(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get rating summary for a product.
    Returns average rating and breakdown by star count.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(ProductReview).filter(ProductReview.product_id == product_id).all()

    if not reviews:
        return ProductRatingSummary(
            product_id=product_id,
            product_name=product.name,
            average_rating=0.0,
            total_reviews=0,
            five_star=0, four_star=0, three_star=0, two_star=0, one_star=0,
        )

    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        counts[r.rating] = counts.get(r.rating, 0) + 1

    avg = sum(r.rating for r in reviews) / len(reviews)

    return ProductRatingSummary(
        product_id=product_id,
        product_name=product.name,
        average_rating=round(avg, 2),
        total_reviews=len(reviews),
        five_star=counts[5],
        four_star=counts[4],
        three_star=counts[3],
        two_star=counts[2],
        one_star=counts[1],
    )


@router.post("/product/{product_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    product_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Submit a product review (any authenticated user).

    - **rating**: 1 to 5 stars
    - **comment**: Optional written feedback

    One review per user per product is allowed.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for duplicate review
    existing = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")

    review = ProductReview(
        product_id=product_id,
        user_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        user_id=review.user_id,
        rating=review.rating,
        comment=review.comment,
        reviewer_name=current_user.full_name or current_user.username,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a review. Users can delete their own; Admins can delete any."""
    review = db.query(ProductReview).filter(ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="You can only delete your own reviews")

    db.delete(review)
    db.commit()
    return None
