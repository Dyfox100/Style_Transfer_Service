#!/bin/sh

#gcloud container clusters get-credentials project-test

docker pull rabbitmq
kubectl create deployment rabbitmq --image=rabbitmq
kubectl expose deployment rabbitmq --port 5672
