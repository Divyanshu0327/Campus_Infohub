import re
from pydantic import BaseModel, field_validator, ValidationInfo
from typing import List, Optional
from datetime import datetime, date

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    id: int

class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None

# User Schemas
class UserBase(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = "Student"

    @field_validator('email')
    def validate_email(cls, v):
        clean = v.strip().lower() if v else ''
        if not EMAIL_REGEX.match(clean):
            raise ValueError('Invalid email format')
        return clean

class UserCreate(UserBase):
    password: str
    reg_no: Optional[str] = None
    course: Optional[str] = None
    batch: Optional[str] = None

    @field_validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Student"
    status: Optional[str] = "Active"
    phone: Optional[str] = None
    reg_no: Optional[str] = None
    course: Optional[str] = None
    batch: Optional[str] = None
    session: Optional[str] = None

    @field_validator('email')
    def validate_email(cls, v):
        clean = v.strip().lower() if v else ''
        if not EMAIL_REGEX.match(clean):
            raise ValueError('Invalid email format')
        return clean


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    reg_no: Optional[str] = None
    course: Optional[str] = None
    batch: Optional[str] = None
    session: Optional[str] = None
    password: Optional[str] = None

    @field_validator('email')
    def validate_email(cls, v):
        if v is not None and len(v.strip()) > 0:
            clean = v.strip().lower()
            if not EMAIL_REGEX.match(clean):
                raise ValueError('Invalid email format (must be valid e.g. user@domain.com)')
            return clean
        return v

    @field_validator('password')
    def validate_password_strength(cls, v):
        if v is not None and len(v.strip()) > 0:
            if len(v.strip()) < 6:
                raise ValueError('Password must be at least 6 characters long')
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    reg_no: Optional[str] = None
    course: Optional[str] = None
    batch: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    current_company: Optional[str] = None
    designation: Optional[str] = None
    previous_company: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator('email')
    def validate_identifier(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Email Address or Enrollment Number is required')
        return clean

class User(UserBase):
    id: int
    created_at: Optional[datetime] = None
    status: Optional[str] = "Pending"
    reg_no: Optional[str] = None
    course: Optional[str] = None
    batch: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    current_company: Optional[str] = None
    designation: Optional[str] = None
    previous_company: Optional[str] = None
    email_verified: Optional[bool] = False
    
    # For flattening profile fields from relationship if needed, or if we added columns to Student?
    # Wait, I added columns to StudentProfile, NOT Student table!
    # Pydantic orm_mode handles relationships object-to-object.
    # If User model maps to Student, and separate table StudentProfile has bio.
    # Student.profile.bio is where it lives.
    # Pydantic won't auto-flatten `profile.bio` to `bio` unless I verify how `orm_mode` handles 1-to-1 flattening or add properties.
    # Actually, in users.py I'm returning `user`. `user` is a Student object.
    # If I want `bio` in the JSON, I need a getter/property or nested schema.
    
    # Let's assume for now I should use a helper or specific Config. Or better:
    # Adding properties to the Student model in models.py to proxy these fields would be easiest for Pydantic.
    # OR update User schema to have `profile: Optional[StudentProfileSchemas]`
    
    # Given the frontend expects flat `bio`, `skills` etc in `user` object (based on EditProfileModal formData state intialization `user?.bio`),
    # flattening is preferred.
    
    class Config:
        orm_mode = True
        from_attributes = True

# Student specific schemas
class StudentAcademicBase(BaseModel):
    enrollment_no: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    # batch is already in User

class StudentAcademic(StudentAcademicBase):
    id: int
    student_id: int

    class Config:
        orm_mode = True

# Post Schemas
class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    user_id: Optional[int] = None
    post_id: int
    created_at: datetime
    user: Optional[User] = None # For embedding user info

    class Config:
        orm_mode = True
        from_attributes = True

    @field_validator('user', mode='before')
    @classmethod
    def populate_admin_user(cls, v, info: ValidationInfo):
        if v is None:
            return {
                "id": 0,
                "name": "System Admin",
                "email": "admin@collegehub.com",
                "role": "admin",
                "status": "Active",
                "created_at": datetime.now()
            }
        return v

class PostBase(BaseModel):
    content: str
    image: Optional[str] = None
    type: Optional[str] = "general"

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    user_id: Optional[int] = None
    likes_count: int
    created_at: datetime
    is_approved: bool = False
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    user: Optional[User] = None
    comments: List[Comment] = []

    class Config:
        orm_mode = True
        from_attributes = True

    @field_validator('user', mode='before')
    @classmethod
    def populate_admin_user(cls, v, info: ValidationInfo):
        if v is None:
            approved_by = info.data.get('approved_by') if (info and hasattr(info, 'data') and info.data) else None
            return {
                "id": 0,
                "name": approved_by or "System Admin",
                "email": "admin@collegehub.com",
                "role": "admin",
                "status": "Active",
                "created_at": datetime.now()
            }
        return v

# Event Schemas
class EventBase(BaseModel):
    title: str
    type: Optional[str] = "Career"
    audience: Optional[str] = "All"
    date: Optional[str] = None
    time: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    organizer: Optional[str] = "Campus InfoHub Committee"
    posted_by: Optional[str] = "Campus InfoHub Committee"
    is_published: Optional[bool] = True
    is_active: Optional[bool] = True

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    attendees: int = 0
    user_rsvp: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    status: Optional[str] = "Upcoming"

    class Config:
        orm_mode = True
        from_attributes = True

# Job Schemas
class JobBase(BaseModel):
    title: str
    company: str
    type: Optional[str] = None
    location: Optional[str] = None
    apply_link: Optional[str] = None
    experience: Optional[str] = "0-2 Years"
    description: Optional[str] = None
    is_active: bool = True

class JobCreate(JobBase):
    posted_by: Optional[str] = None

class Job(JobBase):
    id: int
    posted_date: datetime
    posted_by: Optional[str] = None

    class Config:
        orm_mode = True

# Job Application Schemas
class JobApplicationBase(BaseModel):
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationStatusUpdate(BaseModel):
    status: str  # Applied, Shortlisted, Interviewing, Hired, Rejected
    note: Optional[str] = None

class JobApplicationStatusHistoryItem(BaseModel):
    old_status: Optional[str]
    new_status: str
    changed_at: datetime
    note: Optional[str] = None
    class Config:
        orm_mode = True

class JobApplication(JobApplicationBase):
    id: int
    job_id: int
    student_id: int
    status: str
    applied_date: datetime
    updated_at: Optional[datetime] = None
    student: Optional[User] = None
    job: Optional[Job] = None
    status_history: List[JobApplicationStatusHistoryItem] = []

    class Config:
        orm_mode = True

# Mentorship Schemas
class MentorshipRequestBase(BaseModel):
    mentor_id: int
    message: str

class MentorshipRequestCreate(MentorshipRequestBase):
    pass

class MentorshipRequest(MentorshipRequestBase):
    id: int
    student_id: int
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    mentor_note: Optional[str] = None
    student: Optional[User] = None
    mentor: Optional[User] = None
    sessions: List['MentorshipSession'] = []

    class Config:
        orm_mode = True

# Mentorship Session Schemas
class MentorshipSessionBase(BaseModel):
    topic: str
    scheduled_at: datetime
    duration_minutes: Optional[int] = 60
    notes: Optional[str] = None

class MentorshipSessionCreate(MentorshipSessionBase):
    request_id: int

class MentorshipSessionUpdate(BaseModel):
    status: Optional[str] = None  # Scheduled, Completed, Cancelled
    notes: Optional[str] = None

class MentorshipSession(MentorshipSessionBase):
    id: int
    request_id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# Common Response
class Message(BaseModel):
    message: str

# Notification Schemas
class NotificationBase(BaseModel):
    text: str
    type: Optional[str] = "info"
    read: bool = False

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class ReportCreate(BaseModel):
    target_identifier: Optional[str] = None
    target_id: Optional[int] = None
    target_type: Optional[str] = "User"
    reason: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class ReportAction(BaseModel):
    action: str
    action_taken: Optional[str] = None

class Report(BaseModel):
    id: int
    reporter_id: int
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    target_id: Optional[int] = None
    target_identifier: Optional[str] = None
    target_type: str
    reason: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    action_taken: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# ── Internal Mail Schemas ─────────────────────────────────────────────────────

class InternalMessageCreate(BaseModel):
    recipient_email: str
    subject: str
    body: str

class InternalMessageSender(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    class Config:
        orm_mode = True

class InternalMessageOut(BaseModel):
    id: int
    sender_id: Optional[int] = None
    recipient_id: int
    subject: str
    body: str
    is_read: bool
    is_starred: bool
    created_at: datetime
    sender: Optional[InternalMessageSender] = None
    recipient: Optional[InternalMessageSender] = None

    class Config:
        orm_mode = True


# ── System Settings Schemas ───────────────────────────────────────────────────

class SystemSettingsOut(BaseModel):
    site_name: str
    support_email: str
    maintenance_mode: bool
    allow_registration: bool
    email_notifications: bool
    push_notifications: bool
    theme: str
    primary_color: str

    class Config:
        orm_mode = True

class SystemSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    support_email: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    allow_registration: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    theme: Optional[str] = None
    primary_color: Optional[str] = None


# ── User Stats Schema ─────────────────────────────────────────────────────────

class UserStats(BaseModel):
    posts_count: int
    applications_count: int
    mentorships_count: int
    events_count: int


# ── Admin Activity Schema ─────────────────────────────────────────────────────

class AdminActivityEvent(BaseModel):
    msg: str
    time: str
    type: str  # user | job | post | system | report


# ── Generic Response ──────────────────────────────────────────────────────────

class Message(BaseModel):
    message: str

class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    def validate_password_complexity(cls, v):
        if len(v) < 8 or len(v) > 16:
            raise ValueError('Password must be between 8 and 16 characters in length.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter (A-Z).')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter (a-z).')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number (0-9).')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Password must contain at least one special character.')
        return v


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

    @field_validator('new_password')
    def validate_password_complexity(cls, v):
        if len(v) < 8 or len(v) > 16:
            raise ValueError('Password must be between 8 and 16 characters in length.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter (A-Z).')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter (a-z).')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number (0-9).')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Password must contain at least one special character.')
        return v


class VerifyEmailRequest(BaseModel):
    email: str
    otp: str


class ResendVerificationOTPRequest(BaseModel):
    email: str


# ─── Student Authentication Schemas ──────────────────────────────────────────

class StudentRegisterRequest(BaseModel):
    name: str
    enrollment_no: str
    phone: str
    email: str
    password: str
    confirm_password: str
    course: str
    batch: str
    section: Optional[str] = None

    @field_validator('name')
    def validate_name(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Full Name is required.')
        return clean

    @field_validator('enrollment_no')
    def validate_enrollment(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('University Enrollment Number is required.')
        return clean

    @field_validator('phone')
    def validate_indian_mobile(cls, v):
        clean = v.strip() if v else ''
        if not re.match(r'^[6-9]\d{9}$', clean):
            raise ValueError('Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.')
        return clean

    @field_validator('email')
    def validate_email(cls, v):
        clean = v.strip().lower() if v else ''
        if not EMAIL_REGEX.match(clean):
            raise ValueError('Invalid email format.')
        return clean

    @field_validator('password')
    def validate_password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long.')
        return v


# ─── Notice Schemas ───────────────────────────────────────────────────────────

class NoticeBase(BaseModel):
    title: str
    content: str
    category: str
    target_course: Optional[str] = "All Courses"
    target_audience: str
    is_published: Optional[bool] = True
    published_date: Optional[datetime] = None

class NoticeCreate(NoticeBase):
    @field_validator('title')
    def validate_title(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Notice title is required.')
        return clean

    @field_validator('content')
    def validate_content(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Notice content is required.')
        return clean

    @field_validator('category')
    def validate_category(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Please select a category.')
        allowed = ['Academic', 'Examination', 'Placement', 'General', 'Holiday', 'Event', 'Alumni', 'Other']
        if clean not in allowed:
            raise ValueError(f'Invalid category. Must be one of: {", ".join(allowed)}')
        return clean

    @field_validator('target_course')
    def validate_target_course(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Please select a target course.')
        allowed = ['MCA', 'MBA', 'MTech', 'All Courses']
        if clean not in allowed:
            raise ValueError('Please select a valid target course: MCA, MBA, MTech, or All Courses')
        return clean

    @field_validator('target_audience')
    def validate_target_audience(cls, v):
        clean = v.strip() if v else ''
        if not clean:
            raise ValueError('Please select a target audience.')
        return clean

class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    target_course: Optional[str] = None
    target_audience: Optional[str] = None
    is_published: Optional[bool] = None
    published_date: Optional[datetime] = None

class NoticeOut(BaseModel):
    id: int
    title: str
    content: str
    category: str
    target_course: Optional[str] = "All Courses"
    target_audience: str
    is_published: bool
    published_date: datetime
    posted_by: Optional[str] = "Campus Administration"

    class Config:
        orm_mode = True
        from_attributes = True


# ─── Alumni Schemas ───────────────────────────────────────────────────────────

class AlumniPublicOut(BaseModel):
    id: int
    name: str
    course_completed: str
    year_of_admission: int
    year_of_completion: int
    organization: Optional[str] = None
    designation: Optional[str] = None
    previous_company: Optional[str] = None
    current_city: Optional[str] = None
    professional_picture: Optional[str] = None
    linkedin: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class AlumniAdminOut(BaseModel):
    id: int
    name: str
    enrollment_number: str
    mobile_number: str
    email: str
    date_of_birth: date
    course_completed: str
    year_of_admission: int
    year_of_completion: int
    university_institute: str
    other_institution: Optional[str] = None
    profession: str
    designation: str
    organization: str
    current_city: str
    current_state: str
    current_country: str
    professional_picture: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    x_twitter: Optional[str] = None
    youtube: Optional[str] = None
    willing_to_attend_events: str
    contributions: str
    other_contribution_specify: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class AlumniStatusUpdate(BaseModel):
    status: str  # Active, Pending, Rejected, Inactive



