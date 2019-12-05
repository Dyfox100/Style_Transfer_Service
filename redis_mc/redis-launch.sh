#!/bin/sh

#gcloud container clusters get-credentials lab8

docker pull redis
kubectl create deployment redis --image=redis
kubectl expose deployment redis --port 6379
