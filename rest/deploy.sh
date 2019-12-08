docker build . -t gcr.io/csci5253/rest-server:v1
docker push gcr.io/csci5253/rest-server:v1
kubectl create deployment rest-server --image=gcr.io/csci5253/rest-server:v1
kubectl expose deployment rest-server --type=LoadBalancer --port=5000
