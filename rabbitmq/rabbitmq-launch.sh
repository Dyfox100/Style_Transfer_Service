#!/bin/sh

# First command line argument is name of Kubernetes cluster
#gcloud container clusters get-credentials $1

docker pull rabbitmq
kubectl create deployment rabbitmq --image=rabbitmq
kubectl expose deployment rabbitmq --port 5672
