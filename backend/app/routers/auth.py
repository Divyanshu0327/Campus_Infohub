import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas, utils, database
from ..limiter import limiter
from ..email_service import send_otp_email, send_alumni_approval_email, send_alumni_rejection_email

router = APIRouter(tags=["Authentication"])

# Dummy hash for timing attack mitigation during non-existent user login attempts
DUMMY_HASH = utils.get_password_hash("dummy_password_for_constant_time_security_mitigation")


# ===== OLD STUDENT REGISTRATION/LOGIN CODE - PRESERVED =====
# Original implementation intentionally commented out.
# Can be restored later if required.
#
# @router.post("/register_old", response_model=schemas.Message)
# def register_old(request: Request, user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
#     clean_email = user.email.strip().lower()
#     existing_admin = db.query(models.Admin).filter(func.lower(models.Admin.email) == clean_email).first()
#     if existing_admin: raise HTTPException(status_code=400, detail="This email is already registered.")
#     db_user = db.query(models.Student).filter(func.lower(models.Student.email) == clean_email).first()
#     hashed_password = utils.get_password_hash(user.password)
#     if db_user:
#         if db_user.email_verified: raise HTTPException(status_code=400, detail="This email is already registered.")
#         db_user.name = user.name.strip()
#         db_user.password = hashed_password
#         db_user.email_verified = False
#         db_user.status = "Pending"
#     else:
#         db_user = models.Student(email=clean_email, name=user.name.strip(), password=hashed_password, role="Student", status="Pending", email_verified=False)
#         db.add(db_user)
#     db.commit()
#     return {"message": "Registration initiated."}
# ===== END OLD STUDENT REGISTRATION/LOGIN CODE =====


# ─── New Student Registration & Login Implementation ──────────────────────────

@router.post("/student/register")
@router.post("/register")
@limiter.limit("10/minute")
def student_register(
    request: Request,
    payload: schemas.StudentRegisterRequest,
    db: Session = Depends(database.get_db)
):
    """
    Registers a new student account with server-side validation for email, Indian phone format,
    enrollment number uniqueness, and bcrypt password hashing.
    """
    clean_name = payload.name.strip()
    clean_enrollment = payload.enrollment_no.strip()
    clean_email = payload.email.strip().lower()
    clean_phone = payload.phone.strip()
    clean_course = payload.course.strip()
    clean_batch = payload.batch.strip()
    clean_section = payload.section.strip() if payload.section else None

    # Password match validation
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match."
        )

    # Email uniqueness check
    existing_admin = db.query(models.Admin).filter(
        func.lower(models.Admin.email) == clean_email
    ).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    existing_email_student = db.query(models.Student).filter(
        func.lower(models.Student.email) == clean_email
    ).first()
    if existing_email_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    # Enrollment number uniqueness check
    existing_enrollment = db.query(models.Student).filter(
        models.Student.reg_no == clean_enrollment
    ).first()
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this enrollment number is already registered."
        )

    # Secure Password Hashing
    hashed_password = utils.get_password_hash(payload.password)

    # Create Student record
    new_student = models.Student(
        name=clean_name,
        email=clean_email,
        password=hashed_password,
        phone=clean_phone,
        role="Student",
        status="Active",
        reg_no=clean_enrollment,
        course=clean_course,
        batch=clean_batch,
        section=clean_section,
        email_verified=True
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    # Create default StudentProfile
    profile = models.StudentProfile(
        student_id=new_student.id,
        bio=f"Student pursuing {clean_course} ({clean_batch})",
        location="Campus",
        skills=""
    )
    db.add(profile)
    db.commit()

    # Generate Access Token
    access_token = utils.create_access_token(
        data={"sub": new_student.email, "role": "student", "id": new_student.id},
        expires_delta=timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "message": "Student registration successful!",
        "access_token": access_token,
        "token_type": "bearer",
        "role": "student",
        "id": new_student.id
    }


@router.post("/student/login", response_model=schemas.Token)
@router.post("/token", response_model=schemas.Token)
@limiter.limit("15/minute")
def student_login(
    request: Request,
    user_credentials: schemas.UserLogin,
    db: Session = Depends(database.get_db),
):
    """
    Authenticates students and administrators using email or enrollment number and password.
    Issues JWT access token according to project authentication architecture.
    """
    clean_identifier = user_credentials.email.strip().lower()

    # 1. Check Student Table (by email or enrollment number)
    student = db.query(models.Student).filter(
        or_(
            func.lower(models.Student.email) == clean_identifier,
            models.Student.reg_no == user_credentials.email.strip()
        )
    ).first()

    if student:
        if not utils.verify_password(user_credentials.password, student.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/enrollment number or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if student.status == "Blocked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been suspended. Please contact an administrator.",
            )

        user_role = str(student.role).lower() if student.role else "student"
        access_token = utils.create_access_token(
            data={"sub": student.email, "role": user_role, "id": student.id},
            expires_delta=timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user_role,
            "id": student.id,
        }

    # 2. Check Admin Table
    admin = db.query(models.Admin).filter(
        func.lower(models.Admin.email) == clean_identifier
    ).first()

    if admin:
        if not utils.verify_password(user_credentials.password, admin.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = utils.create_access_token(
            data={"sub": admin.email, "role": "admin", "id": admin.id},
            expires_delta=timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "admin",
            "id": admin.id,
        }

    # 3. Check Alumni Table (dedicated alumni directory accounts)
    alumni_user = db.query(models.Alumni).filter(
        func.lower(models.Alumni.email) == clean_identifier
    ).first()

    if alumni_user:
        # Block if no password was set (old records before password field was added)
        if not alumni_user.password:
            utils.verify_password(user_credentials.password, DUMMY_HASH)  # timing mitigation
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your alumni account does not have a portal password set. Please contact the administration.",
            )

        if not utils.verify_password(user_credentials.password, alumni_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Status gate — only Active alumni can log in
        if alumni_user.status == "Pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your alumni registration is pending admin approval. You will receive an email once your account is activated.",
            )

        if alumni_user.status == "Rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your alumni registration was not approved. Please contact the administration for further information.",
            )

        if alumni_user.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your alumni account is not active. Please contact the administration.",
            )

        access_token = utils.create_access_token(
            data={"sub": alumni_user.email, "role": "alumni", "id": alumni_user.id},
            expires_delta=timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "alumni",
            "id": alumni_user.id,
        }

    # Timing Attack Mitigation
    utils.verify_password(user_credentials.password, DUMMY_HASH)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email/enrollment number or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/verify-email", response_model=schemas.Message)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    payload: schemas.VerifyEmailRequest,
    db: Session = Depends(database.get_db),
):
    """
    Verify 6-digit registration OTP, mark email_verified = True, keep status = Pending for admin approval,
    and invalidate/delete the OTP record.
    """
    clean_email = payload.email.strip().lower()
    user_otp = payload.otp.strip()

    otp_record = (
        db.query(models.OTP)
        .filter(
            func.lower(models.OTP.email) == clean_email,
            models.OTP.purpose == "EMAIL_VERIFICATION",
            models.OTP.is_used == False
        )
        .order_by(models.OTP.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please request a new OTP."
        )

    # Attempt limit check (max 5 attempts)
    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP verification attempts exceeded. Please request a new verification code."
        )

    otp_record.attempts += 1
    db.commit()

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now > exp:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification OTP code has expired (valid for 5 minutes). Please request a new code."
        )

    if otp_record.otp != user_otp:
        remaining = max(0, 5 - otp_record.attempts)
        if otp_record.attempts >= 5:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum OTP verification attempts exceeded. Please request a new verification code."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect verification code. {remaining} attempt(s) remaining."
        )

    # OTP is valid -> Mark used & delete/invalidate
    otp_record.is_used = True

    student = db.query(models.Student).filter(
        func.lower(models.Student.email) == clean_email
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )

    student.email_verified = True
    student.status = "Pending"  # Requires Admin Approval before activation

    # Create default StudentProfile if missing
    existing_profile = db.query(models.StudentProfile).filter(models.StudentProfile.student_id == student.id).first()
    if not existing_profile:
        profile = models.StudentProfile(
            student_id=student.id,
            bio="Student at Campus InfoHub (Pending Approval)",
            location="Campus",
            skills=""
        )
        db.add(profile)

    db.commit()
    return {"message": "Email verified successfully! Your account registration has been submitted for Admin approval."}


@router.post("/resend-verification-otp", response_model=schemas.Message)
@limiter.limit("5/minute")
def resend_verification_otp(
    request: Request,
    payload: schemas.ResendVerificationOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Resend 6-digit registration OTP with 60-second cooldown support on frontend.
    Invalidates previous OTP and generates a brand new OTP.
    """
    clean_email = payload.email.strip().lower()

    student = db.query(models.Student).filter(
        func.lower(models.Student.email) == clean_email
    ).first()

    if not student:
        return {"message": "If an unverified account with that email exists, a new OTP code has been sent."}

    if student.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your email is already verified. You may sign in directly."
        )

    # Invalidate previous unused registration OTPs for this email
    db.query(models.OTP).filter(
        func.lower(models.OTP.email) == clean_email,
        models.OTP.purpose == "EMAIL_VERIFICATION",
        models.OTP.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    otp_code = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    reg_otp = models.OTP(
        email=clean_email,
        otp=otp_code,
        purpose="EMAIL_VERIFICATION",
        attempts=0,
        is_used=False,
        expires_at=expires_at
    )
    db.add(reg_otp)
    db.commit()

    background_tasks.add_task(send_otp_email, clean_email, otp_code, "EMAIL_VERIFICATION")

    return {"message": "A new 6-digit verification code has been sent to your email."}


@router.post("/forgot-password", response_model=schemas.Message)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Initiate email OTP password reset flow using reusable OTP model.
    Generates a secure 6-digit OTP valid for 5 minutes, invalidates previous OTPs,
    and sends email via Gmail SMTP without revealing if user exists.
    """
    clean_email = payload.email.strip().lower()

    student = db.query(models.Student).filter(
        func.lower(models.Student.email) == clean_email
    ).first()
    admin = None
    alumni_user = None
    if not student:
        admin = db.query(models.Admin).filter(
            func.lower(models.Admin.email) == clean_email
        ).first()
    if not student and not admin:
        alumni_user = db.query(models.Alumni).filter(
            func.lower(models.Alumni.email) == clean_email
        ).first()

    if student or admin or alumni_user:
        # Invalidate previous unused PASSWORD_RESET OTPs for this email
        db.query(models.OTP).filter(
            func.lower(models.OTP.email) == clean_email,
            models.OTP.purpose == "PASSWORD_RESET",
            models.OTP.is_used == False
        ).update({"is_used": True}, synchronize_session=False)

        otp_code = f"{secrets.randbelow(1000000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        otp_record = models.OTP(
            email=clean_email,
            otp=otp_code,
            purpose="PASSWORD_RESET",
            attempts=0,
            is_used=False,
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()

        background_tasks.add_task(send_otp_email, clean_email, otp_code, "PASSWORD_RESET")

    return {"message": "If an account with that email exists, an OTP has been sent."}


@router.post("/verify-otp", response_model=schemas.Message)
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    payload: schemas.VerifyOTPRequest,
    db: Session = Depends(database.get_db),
):
    """
    Verify the 6-digit OTP code for password reset submitted by the user.
    """
    clean_email = payload.email.strip().lower()
    user_otp = payload.otp.strip()

    otp_record = (
        db.query(models.OTP)
        .filter(
            func.lower(models.OTP.email) == clean_email,
            models.OTP.purpose == "PASSWORD_RESET",
            models.OTP.is_used == False
        )
        .order_by(models.OTP.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please request a new one."
        )

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP verification attempts exceeded. Please request a new OTP."
        )

    otp_record.attempts += 1
    db.commit()

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now > exp:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired (valid for 5 minutes). Please request a new one."
        )

    if otp_record.otp != user_otp:
        remaining = max(0, 5 - otp_record.attempts)
        if otp_record.attempts >= 5:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum OTP verification attempts exceeded. Please request a new OTP."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect OTP code. {remaining} attempt(s) remaining."
        )

    return {"message": "OTP verified successfully. You may now reset your password."}


@router.post("/reset-password", response_model=schemas.Message)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    payload: schemas.ResetPasswordRequest,
    db: Session = Depends(database.get_db),
):
    """
    Reset user password after OTP verification.
    Hashes new password with bcrypt and invalidates the OTP.
    """
    clean_email = payload.email.strip().lower()
    user_otp = payload.otp.strip()

    otp_record = (
        db.query(models.OTP)
        .filter(
            func.lower(models.OTP.email) == clean_email,
            models.OTP.purpose == "PASSWORD_RESET",
            models.OTP.is_used == False
        )
        .order_by(models.OTP.created_at.desc())
        .first()
    )

    if not otp_record or otp_record.otp != user_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP authorization. Please restart password reset process."
        )

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now > exp:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired. Please request a new one."
        )

    user = db.query(models.Student).filter(
        func.lower(models.Student.email) == clean_email
    ).first()
    if not user:
        user = db.query(models.Admin).filter(
            func.lower(models.Admin.email) == clean_email
        ).first()
    if not user:
        user = db.query(models.Alumni).filter(
            func.lower(models.Alumni.email) == clean_email
        ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )

    hashed_pwd = utils.get_password_hash(payload.new_password)
    user.password = hashed_pwd
    otp_record.is_used = True

    db.commit()
    return {"message": "Password reset successfully. Please sign in with your new password."}


@router.post("/cleanup-pending", response_model=schemas.Message)
def cleanup_pending_and_otps(
    db: Session = Depends(database.get_db)
):
    """
    Cleanup utility for expired OTP records and unverified pending accounts older than 24 hours.
    """
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    # 1. Invalidate/Delete expired OTPs
    deleted_otps = db.query(models.OTP).filter(
        (models.OTP.expires_at < now) | (models.OTP.is_used == True)
    ).delete(synchronize_session=False)

    # 2. Clean unverified pending accounts older than 24 hours
    pending_students = db.query(models.Student).filter(
        models.Student.email_verified == False,
        models.Student.status == "Pending",
        models.Student.created_at < cutoff_24h
    ).all()

    deleted_users = len(pending_students)
    for student in pending_students:
        db.delete(student)

    db.commit()
    return {"message": f"Cleanup complete: removed {deleted_otps} OTP records and {deleted_users} unverified pending accounts older than 24 hours."}
