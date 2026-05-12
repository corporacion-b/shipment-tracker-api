import pytest
from datetime import timedelta
from jose import jwt
from src.core.security import hash_password, verify_password, create_access_token
from src.core.config import settings

def test_password_hashing():
    """Verifica que las contraseñas se encripten y validen correctamente."""
    password = "mi_clave_secreta_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("otra_clave", hashed) is False

def test_create_access_token():
    """Verifica la creación y contenido del token JWT."""
    subject = "tester@example.com"
    # Pasamos el subject directamente
    token = create_access_token(subject)
    
    payload = jwt.decode(
        token, 
        settings.JWT_SECRET_KEY, 
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    # Ahora 'sub' será exactamente el string "tester@example.com"
    assert payload.get("sub") == subject
    assert "exp" in payload

def test_token_expired_check():
    """Verifica que el token expire correctamente."""
    from datetime import timedelta
    subject = "expired@test.com"
    
    # PASO POSICIONAL: 
    # Si tu función es def create_access_token(subject, expires), 
    # enviarlo sin el nombre evitará el TypeError.
    token = create_access_token(subject, expires_delta=timedelta(minutes=-1))
        
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )