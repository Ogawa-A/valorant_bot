from venv import create
import cv2
import tempfile
import os
import rso_request
import shop

riot_development_api_key = "RGAPI-745aa212-6761-4607-ae17-1fb99f5106df"
     

username = 's1eamed'
password = '7875belle'

auth_data = rso_request.get_rso_data(username, password)
print(auth_data)
skin_data = shop.get_skin_data(auth_data)


