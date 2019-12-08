#takes in gcr.io/csci5253/rest-server:v1
docker build . -t $1
docker push $1
kubectl create deployment rest-server --image=$1
kubectl expose deployment rest-server --type=LoadBalancer --port=5000
kubectl set image deployment rest-server rest-server=$1
