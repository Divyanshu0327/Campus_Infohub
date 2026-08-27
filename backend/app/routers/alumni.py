import os
import re
import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from .. import models, schemas, database
from ..limiter import limiter

router = APIRouter(prefix="/api/alumni", tags=["Alumni Directory"])

MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

# ─── Public Endpoint ──────────────────────────────────────────────────────────

@router.get("/public", response_model=List[schemas.AlumniPublicOut])
@router.get("/public-list", response_model=List[schemas.AlumniPublicOut])
def get_public_alumni(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db)
):
    """
    Returns only safe public fields for the landing page.
    Never exposes sensitive data like DOB, phone, email, or internal status.
    """
    alumni_list = (
        db.query(models.Alumni)
        .filter(models.Alumni.status == "Active")
        .order_by(models.Alumni.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Fallback to Student table if no records in Alumni table yet
    if not alumni_list:
        student_alumni = (
            db.query(models.Student)
            .filter(models.Student.role == "Alumni", models.Student.status == "Active")
            .offset(skip)
            .limit(limit)
            .all()
        )
        result = []
        for s in student_alumni:
            batch_end = s.batch.split("-")[-1].strip() if s.batch and "-" in s.batch else "2024"
            year_val = int(batch_end) if batch_end.isdigit() else 2024
            result.append(
                schemas.AlumniPublicOut(
                    id=s.id,
                    name=s.name,
                    course_completed=s.course or "GGSIPU Graduate",
                    year_of_completion=year_val,
                    organization=s.company or "Industry Professional",
                    designation=s.designation or "Alumnus",
                    current_city=s.location or "Delhi NCR",
                    university_institute="GGSIPU",
                    professional_picture=s.avatar
                )
            )
        return result

    return [
        schemas.AlumniPublicOut(
            id=a.id,
            name=a.name,
            course_completed=a.course_completed,
            year_of_admission=a.year_of_admission,
            year_of_completion=a.year_of_completion,
            professional_picture=a.professional_picture,
            linkedin=a.linkedin
        )
        for a in alumni_list
    ]


# ─── Alumni Registration Endpoint ─────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_alumni(
    name: str = Form(...),
    enrollment_number: str = Form(...),
    mobile_number: str = Form(...),
    email: str = Form(...),
    date_of_birth: str = Form(...),
    course_completed: str = Form(...),
    year_of_admission: int = Form(...),
    year_of_completion: int = Form(...),
    university_institute: Optional[str] = Form("NA"),
    other_institution: Optional[str] = Form("NA"),
    profession: str = Form(...),
    designation: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    current_city: str = Form(...),
    current_state: str = Form(...),
    current_country: str = Form("India"),
    linkedin: Optional[str] = Form(None),
    facebook: Optional[str] = Form(None),
    instagram: Optional[str] = Form(None),
    x_twitter: Optional[str] = Form(None),
    youtube: Optional[str] = Form(None),
    willing_to_attend_events: str = Form(...),
    contributions: str = Form(...),  # Comma-separated strings
    other_contribution_specify: Optional[str] = Form(None),
    professional_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db)
):
    """
    Registers a new Alumnus with strict validation, duplicate prevention, and optional 1 MB image upload.
    """
    clean_name = name.strip()
    clean_enrollment = enrollment_number.strip()
    clean_email = email.strip().lower()
    clean_mobile = mobile_number.strip()
    clean_course = course_completed.strip()

    # 1. Required text validations
    if not clean_name or not clean_enrollment or not clean_mobile or not clean_email:
        raise HTTPException(status_code=400, detail="Name, Enrollment Number, Mobile Number, and Email are required.")

    # 2. Course validation (Must be MCA, MBA, or MTech)
    if clean_course not in ["MCA", "MBA", "MTech"]:
        raise HTTPException(status_code=400, detail="Course Completed must be one of: MCA, MBA, MTech.")

    # 3. Dynamic Admission & Completion Year Validation
    current_year = datetime.now().year
    min_admission_year = 2004
    max_admission_year = current_year - 2

    min_completion_year = year_of_admission + 2
    max_completion_year = current_year

    if year_of_admission < min_admission_year or year_of_admission > max_admission_year:
        raise HTTPException(status_code=400, detail=f"Year of admission must be between {min_admission_year} and {max_admission_year}.")

    if year_of_completion < min_completion_year or year_of_completion > max_completion_year:
        raise HTTPException(status_code=400, detail=f"Year of completion must be between {min_completion_year} and {max_completion_year}.")

    # 5. Email format validation
    if not EMAIL_REGEX.match(clean_email):
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    # 6. Mobile format validation (India 10 digits or International with country code)
    if not re.match(r'^(?:\+?\d{1,4}[-.\s]?)?\d{10}$', clean_mobile):
        raise HTTPException(status_code=400, detail="Please provide a valid 10-digit mobile number or international phone number.")

    # 7. Duplicate Check
    existing_alumni = db.query(models.Alumni).filter(
        or_(
            func.lower(models.Alumni.email) == clean_email,
            models.Alumni.enrollment_number == clean_enrollment
        )
    ).first()

    if existing_alumni:
        raise HTTPException(
            status_code=409,
            detail="An alumni record with this email or enrollment number already exists."
        )

    # 6. Date of Birth parsing
    parsed_dob = None
    try:
        parsed_dob = datetime.strptime(date_of_birth.strip(), "%Y-%m-%d").date()
    except ValueError:
        try:
            parsed_dob = datetime.strptime(date_of_birth.strip(), "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Date of Birth format. Please use YYYY-MM-DD.")

    # 7. Institute Logic
    clean_institute = university_institute.strip()
    clean_other_inst = (other_institution or "").strip()
    if clean_institute == "Any Other":
        if not clean_other_inst or clean_other_inst.upper() == "NA":
            raise HTTPException(status_code=400, detail="Please specify the institution name under 'Any Other Institution'.")
    else:
        clean_other_inst = "NA"

    # 8. Profession Logic
    clean_profession = profession.strip()
    clean_designation = (designation or "").strip()
    clean_organization = (organization or "").strip()

    if clean_profession in ["Home Maker", "Unemployed"]:
        clean_designation = "NA"
        clean_organization = "NA"
    elif clean_profession == "Studying":
        if not clean_designation or clean_designation.upper() == "NA":
            raise HTTPException(status_code=400, detail="Please specify the degree currently being pursued under Designation.")
        if not clean_organization or clean_organization.upper() == "NA":
            raise HTTPException(status_code=400, detail="Please specify the institution name under Organization/Institution.")
    else:
        if not clean_designation or clean_designation.upper() == "NA":
            raise HTTPException(status_code=400, detail=f"Designation is required for profession: {clean_profession}.")
        if not clean_organization or clean_organization.upper() == "NA":
            raise HTTPException(status_code=400, detail=f"Organization/Institution name is required for profession: {clean_profession}.")

    # 9. Contribution Logic
    contrib_list = [c.strip() for c in contributions.split(",") if c.strip()]
    if "Unable to Contribute" in contrib_list:
        contrib_list = ["Unable to Contribute"]
        clean_other_contrib = None
    else:
        clean_other_contrib = (other_contribution_specify or "").strip() if "Other" in contrib_list else None
        if "Other" in contrib_list and not clean_other_contrib:
            raise HTTPException(status_code=400, detail="Please specify your contribution details under 'Please specify'.")

    # 10. Social Media URLs Validation
    for label, link in [("LinkedIn", linkedin), ("Facebook", facebook), ("Instagram", instagram), ("X", x_twitter), ("YouTube", youtube)]:
        if link and link.strip():
            clean_link = link.strip()
            if not clean_link.startswith("http://") and not clean_link.startswith("https://"):
                clean_link = "https://" + clean_link
            if not URL_REGEX.match(clean_link):
                raise HTTPException(status_code=400, detail=f"Please enter a valid URL for {label}.")

    # 11. Image Upload Processing
    saved_picture_path = None
    if professional_picture and professional_picture.filename:
        # Check Content-Type / MIME
        if professional_picture.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type for professional picture. Only JPEG, PNG, and WebP images are allowed."
            )

        # Check File Extension
        ext = os.path.splitext(professional_picture.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Invalid file extension. Only .jpg, .jpeg, .png, and .webp files are supported."
            )

        # Read contents to check file size <= 1 MB
        contents = await professional_picture.read()
        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Uploaded file size exceeds the 1 MB maximum limit."
            )

        # Save file to uploads directory
        uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "uploads", "alumni_photos")
        os.makedirs(uploads_dir, exist_ok=True)

        safe_filename = f"alumni_{uuid.uuid4().hex}{ext}"
        full_filepath = os.path.join(uploads_dir, safe_filename)

        with open(full_filepath, "wb") as f:
            f.write(contents)

        saved_picture_path = f"/uploads/alumni_photos/{safe_filename}"

    # 12. Create Alumni Record
    new_alumni = models.Alumni(
        name=clean_name,
        enrollment_number=clean_enrollment,
        mobile_number=clean_mobile,
        email=clean_email,
        date_of_birth=parsed_dob,
        course_completed=clean_course,
        year_of_admission=year_of_admission,
        year_of_completion=year_of_completion,
        university_institute=clean_institute,
        other_institution=clean_other_inst,
        profession=clean_profession,
        designation=clean_designation,
        organization=clean_organization,
        current_city=current_city.strip(),
        current_state=current_state.strip(),
        current_country=current_country.strip() or "India",
        professional_picture=saved_picture_path,
        linkedin=linkedin.strip() if linkedin else None,
        facebook=facebook.strip() if facebook else None,
        instagram=instagram.strip() if instagram else None,
        x_twitter=x_twitter.strip() if x_twitter else None,
        youtube=youtube.strip() if youtube else None,
        willing_to_attend_events=willing_to_attend_events.strip(),
        contributions=",".join(contrib_list),
        other_contribution_specify=clean_other_contrib,
        status="Active"
    )

    db.add(new_alumni)
    db.commit()
    db.refresh(new_alumni)

    return {
        "message": "Alumni Registration completed successfully!",
        "alumni_id": new_alumni.id
    }
