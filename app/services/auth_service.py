from datetime import timedelta
from flask import abort

from app.database import db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token

from app.models.user_profile import UserProfile

# Store unverified registrations in memory
# Key: email, Value: dict containing hashed_password, name, otp, expires_at
from typing import Any, Dict
pending_registrations: Dict[str, Dict[str, Any]] = {}

def register_user(email: str, password: str, name: str | None = None) -> None:
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        abort(400, description="Email already registered")

    # Store registration details in memory
    hashed_password = get_password_hash(password)
    
    # Generate OTP
    import random
    from datetime import datetime, timezone, timedelta
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    pending_registrations[email] = {
        'hashed_password': hashed_password,
        'name': name,
        'otp': otp,
        'expires_at': expires_at
    }
    
    # Send OTP
    from app.services.email_service import send_otp_email
    send_otp_email(
        to_email=email, 
        otp=otp, 
        subject="Verify your Resume2Interview account", 
        title="Verify Your Account", 
        instructions="Thank you for registering! Please enter the following 6-digit code to activate your account."
    )
    return None

def resend_registration_otp(email: str) -> None:
    """Re-generate & re-send the OTP for a pending (unverified) registration."""
    import random
    from datetime import datetime, timezone, timedelta

    if email not in pending_registrations:
        # Silently succeed — don't reveal whether the email is known
        return

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    pending_registrations[email]['otp'] = otp
    pending_registrations[email]['expires_at'] = expires_at

    from app.services.email_service import send_otp_email
    send_otp_email(
        to_email=email,
        otp=otp,
        subject="New Resume2Interview verification code",
        title="New Verification Code",
        instructions="Here is your new 6-digit verification code. The previous code has been invalidated."
    )

def verify_registration(email: str, otp: str) -> dict:
    from datetime import datetime, timezone
    
    # First check if user is in pending registrations
    if email not in pending_registrations:
        # Check if they are already in the DB and verified
        user = User.query.filter_by(email=email).first()
        if user:
            if getattr(user, 'is_verified', False):
                abort(400, description="User is already verified")
            else:
                # Handle legacy unverified users in DB if needed; for now, let's just use the cache.
                abort(404, description="Registration session not found. Please register again.")
        abort(404, description="Registration session not found")
        
    pending_data = pending_registrations[email]
        
    if pending_data['otp'] != otp:
        abort(400, description="Invalid OTP")
        
    expires_at = pending_data['expires_at']
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if not expires_at or expires_at < datetime.now(timezone.utc):
        pending_registrations.pop(email, None)
        abort(400, description="OTP expired")
        
    # Valid code -> Create the user in the database now
    new_user = User(
        email=email, 
        hashed_password=pending_data['hashed_password'],
        is_verified=True,
    )
    db.session.add(new_user)
    db.session.flush() # get ID before commit
    
    profile = UserProfile(user_id=new_user.id, full_name=pending_data.get('name'))
    db.session.add(profile)
    
    db.session.commit()
    
    # Clear from pending
    pending_registrations.pop(email, None)
    
    # Return access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(email: str, password: str) -> dict:
    user = User.query.filter_by(email=email).first()
    if not user:
        abort(401, description="Email does not exist")
    
    if not verify_password(password, user.hashed_password):
        abort(401, description="Password mismatch")
        
    if not getattr(user, 'is_verified', True):
        abort(403, description="Account not verified. Please verify your email first.")
    
    # Generate token (60 min expiration)
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def request_password_reset(email: str) -> None:
    from datetime import datetime, timezone, timedelta
    import random
    import string
    
    user = User.query.filter_by(email=email).first()
    if not user:
        # Silently succeed to prevent email enumeration
        return
        
    code = str(random.randint(100000, 999999))
    user.reset_code = code
    user.reset_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.session.commit()
    
    from app.services.email_service import send_otp_email

    success = send_otp_email(
        to_email=email, 
        otp=code, 
        subject="Resume2Interview Password Reset", 
        title="Password Reset", 
        instructions="We received a request to reset the password for your account. Please enter the following 6-digit code in the app to proceed:"
    )
    if not success:
        # We still silently fail for unregistered emails, but if the email failed
        # to send due to SMTP configuration, we should let the user know.
        abort(500, description="Error dispatching reset email. Check server configuration.")

def reset_password(email: str, code: str, new_password: str) -> None:
    from datetime import datetime, timezone
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.reset_code or user.reset_code != code:
        abort(400, description="Invalid reset code")
        
    # Ensure code isn't expired
    expires_at = user.reset_code_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if not expires_at or expires_at < datetime.now(timezone.utc):
        abort(400, description="Reset code expired")
        
    # Valid code -> Update password -> Clear token
    user.hashed_password = get_password_hash(new_password)
    user.reset_code = None
    user.reset_code_expires_at = None
    db.session.commit()
