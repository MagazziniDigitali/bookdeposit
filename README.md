
curl -X POST  -F bag=@test/bag.test.zip http://localhost:5000/api/v1/upload

http POST -f bag=@test/bag.test.zip :5000/api/v1/upload

http -p HBhb POST :5000/auth username=raffaele password=messuti

 http --auth-type=jwt --auth=$JWT :5000/protected





export JWT=$(http POST :5000/api/v1/auth username=raffaele password=messuti | jq -r .access_token):

http --auth-type=jwt --auth=$JWT -f POST  :5000/api/v1/upload bag@test.data/bag.test.zip