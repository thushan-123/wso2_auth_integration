from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from .config import settings
from .db import get_session
from .models import User
from sqlmodel import select
from urllib.parse import urlencode
from datetime import datetime

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="asgardeo",
    client_id=settings.ASGARDEO_CLIENT_ID,
    client_secret=settings.ASGARDEO_CLIENT_SERECT,  # (typo kept for consistency)
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"{settings.ASGARDEO_DOMAIN}/.well-known/openid-configuration",
)

@router.get("/login")
async def login(request: Request):
    redirect_uri = str(settings.ASGARDEO_CALLBACK_URL)
    return await oauth.asgardeo.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def callback(request: Request, session=Depends(get_session)):
    token = await oauth.asgardeo.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.asgardeo.parse_id_token(request, token)

    auth0_sub = userinfo.get("sub")  # still fine, sub is standard OIDC
    email = userinfo.get("email")

    db_user = session.exec(select(User).where(User.auth0_sub == auth0_sub)).first()
    if not db_user:
        db_user = User(auth0_sub=auth0_sub, email=email)
        session.add(db_user)
    else:
        db_user.email = email or db_user.email
        db_user.updated_at = datetime.utcnow()
    session.commit()

    request.session["user"] = {
        "sub": auth0_sub,
        "email": email,
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }
    return RedirectResponse(url="/profile", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    params = {
        "client_id": settings.ASGARDEO_CLIENT_ID,
        "returnTo": str(request.url_for("index"))
    }
    # Asgardeo logout endpoint
    url = f"{settings.ASGARDEO_DOMAIN}/oidc/logout?{urlencode(params)}"
    return RedirectResponse(url=url)

def require_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return user
