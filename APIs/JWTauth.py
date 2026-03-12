from typing import Union

from fastapi import FastAPI

import jwt
from jwt import ExpiredSignatureError
from datetime import datetime, timedelta
from pydantic import BaseModel
from datetime import datetime,timezone
import environ, os # for local running, env key reads
from pathlib import Path

env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

app = FastAPI()

SECRET_KEY = env("TOKEN_SECRET")
EXPIRATION_TIME = 60

class UserData(BaseModel):
    sub: str
    nickname: str
    channel_req: float
    cast_receive: bool

# Implement the JWT token generators and verification here
class Token(BaseModel):
    token: str

@app.get("/")
def read_root(body: Token):
    print(body.token)
    return {"Hello": "World"}

# Example, remove this later
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}

# Called when a token is not already in use for casting/listening, server generates and returns a valid JWT token.
@app.post("/token")
def get_a_token(userReq: UserData):
    # Set up expiration time
    # TODO: since channels do not have to be limited anymore to a range, is this necessary to have?
    token_time_limit = str(datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_TIME))

    # Create payload
    # TODO: go back and reevaluate what the payload should be, requirements have changed.
    payload_data = {
        "sub": userReq.sub,
        "name": userReq.nickname,  # name ident
        "cast_receive": userReq.cast_receive,  # if the user wants to cast, True. If "receive", false.
        "channel_req": userReq.channel_req,  # channel to operate on
        "timestamp": token_time_limit # timestamp of current request
    }

    my_secret = SECRET_KEY

    # Encode JWT, send back.
    token = jwt.encode(
        payload=payload_data,
        key=my_secret
    )

    return {"token": token, "timelimit": token_time_limit}

@app.get("/verify")
def verify_a_token(token: Token):
    # verify a token sent here with the secret, return if verified + return the addr of the EC2 instance so the user can connect.
    # Since we'll receive a payload, get the channel from the payload and give it to the server so it can keep it in the list of users to send/recv
    print("Test")
    try:
        header_data = jwt.get_unverified_header(token)
        jwt.decode(token, key=SECRET_KEY, algorithms=header_data['alg'])
    except ExpiredSignatureError as e:
        print("Error:\n"+str(e))
        return {"result": "Cannot decode token to connect to the server. Something is wrong with the auth token itself."}
    return {"result": "Token established."}

@app.post("/getinst")
def get_server():
    # Verify the token being sent in, then allow users to connect to the EC2 instance by retrieving its address.
    # TODO: finish this.
    return {}