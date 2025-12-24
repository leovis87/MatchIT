from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os

# JWT => HEADER.PAYLOAD.SIGNATURE

ALG = 'HS256' # 암호화 알고리즘 
SECRET = os.getenv("JWT_SECRET", "my-secret")
# HACKER = "secret"

def create_token(user_info):
    payload = {
        'user_info': user_info,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(seconds=5) # 만료 시간 30분
    } # 키값: exp 값: datetime utc 
    
    # 암호화 토큰 생성
    token = jwt.encode(payload, SECRET, algorithm=ALG) 
    return token

def create_refresh_token(user_info):
    payload = {
        'user_info': user_info,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + timedelta(days=7) # 만료 시간 30분
    } # 키값: exp 값: datetime utc 
    
    # 암호화 토큰 생성
    token = jwt.encode(payload, SECRET, algorithm=ALG) 
    return token

def verify_token(token):
    try:
        # 토큰을 해독 
        payload = jwt.decode(token, SECRET, algorithms=ALG)
        
        user_info = payload.get('user_info', None)
        
        return user_info, None
    except jwt.ExpiredSignatureError:
        # 만약에 만료되었을 때 에러 처리
        return None, 'expired'
    except JWTError: 
        # 유효하지 않은 토큰일 때 에러 처리
        return None, 'invalid'
     
# payload에 있는 사용자 정보 / 만료인지, 유효하지 않은 건지, 유효한거지
     
# print(verify_token(token))

# payload = jwt.decode(token, HACKER, algorithms=ALG)
# user_info = payload.get('user_info', None)
# print(user_info)

# a, b = verify_token(token)
# print(a, b)