#curl -H "Authorization: Bearer $(curl -X POST -d "username=alexandre&password=a" http://localhost:8000/api-token-auth/ | awk -F"\"" '{print $4}')" -d '{"role":"user_1"'  "http://localhost:4000/nodes?limit=1"
curl -X POST -d "username=alexandre&password=a" http://localhost:8000/api-token-auth/ | awk -F"\"" '{print $4}'
