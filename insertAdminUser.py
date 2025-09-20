import bcrypt
import mysql.connector




heslo = 'marcel'
hesloHASH = bcrypt.hashpw(heslo.encode('utf-8'), bcrypt.gensalt())

nove_heslo = 'marcel'
if bcrypt.checkpw(nove_heslo.encode('utf-8'), hesloHASH):  # Ověření hashovaného hesla)
    print('FUNGUJE')
else:
    print("NE-FUNGUJE")



  
# example password 
password = 'marcel'
  
# converting password to array of bytes 
bytes = password.encode('utf-8') 
  
# generating the salt 
salt = bcrypt.gensalt() 
  
# Hashing the password 
hash = bcrypt.hashpw(bytes, salt) 
  
# Taking user entered password  
userPassword =  'marcel'
  
# encoding user password 
userBytes = userPassword.encode('utf-8') 
  
# checking password 
result = bcrypt.checkpw(userBytes, hash) 
  
print(result)