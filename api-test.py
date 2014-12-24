import urllib
import urllib2 
import time

baseurl = "https://start.exactonline.nl"
application_id = "a90e5d42-6e86-439b-aff2-9a4bad63596b"

division = "750740"

raw_params = {'_UserName_':'mm@trash-mail.com','_Password_':'ES1ma87e!'}


params = urllib.urlencode(raw_params)



opener = urllib2.build_opener()
opener.addheaders = [("Content-Type","application/x-www-form-urlencoded")]
opener.addheaders = [("Connection","Keep-Alive")]

url = baseurl+"/docs/XMLDivisions.aspx"
response = opener.open(url,params)

cookie = response.headers.get('Set-Cookie')

print cookie 
time.sleep(5)
url = baseurl+"/docs/ClearSession.aspx?Division="+division+"&Remember=3";

opener.addheaders = [("cookie", str(cookie))]
response = opener.open(url)

print response.read()
time.sleep(5)
#url = baseurl+"/docs/XMLUpload.aspx?Topic=Accounts&ApplicationKey="+application_id;
url = baseurl+"/docs/XMLUpload.aspx?Topic=GLTransactions&ApplicationKey="+application_id;

#myfile = open("./OUTPUT/Relaties.xml","r")
myfile = open("./OUTPUT/GLTransactions3.xml","r")
data = myfile.read()
print data

response = opener.open(url ,data)


print response.read()