import os
import dotenv
import requests
dotenv.load_dotenv()
import datetime
from database.db_config import get_token_collection


def get_access_token():
    body = {
        "client_id":os.getenv("CLIENT_ID"),
        "client_secret":os.getenv("CLIENT_SECRET"),
        "refresh_token":os.getenv("REFRESH_TOKEN"),
        "grant_type":"refresh_token",
    }
    try:

       response = requests.post("https://accounts.zoho.com/oauth/v2/token",data=body)
       print("Raw response:", response.text)
       data = response.json()
       access_token = data
       return access_token
    except Exception as e:
       print("error raised while getting access token",e)


async def token_validator():
    try:
        token = await get_token_collection().find({}).to_list()
        if token:
            #if token is there check if the token is valid or not
            expiry_time = token[0].get('expires_in')
            if expiry_time < datetime.datetime.now():
                print("token expired")
                #remove the old token from the collection generate the new token and save it to the db
                await get_token_collection().delete_many({})
                token = get_access_token()
                print(token)
                current_time = datetime.datetime.now()
                combined_time = current_time + datetime.timedelta(seconds=token.get('expires_in'))
                print(combined_time)
                token.update({'expires_in': combined_time})
                await get_token_collection().insert_one(token)
                print("Token successfully inserted")
                return token.get('access_token')
            else:
                #Token is valid pass it to the controller
                print("token valid")
                return token[0].get("access_token")

        else:
            #fetch the new token and save it to the db
            token = get_access_token()
            print(token)
            current_time = datetime.datetime.now()
            combined_time = current_time + datetime.timedelta(seconds=token.get('expires_in'))
            print(combined_time)
            token.update({'expires_in':combined_time})
            await get_token_collection().insert_one(token)
            print("Token successfully inserted")
            return token.get('access_token')
    except Exception as e:
        print("error raised while getting access token",e)





