#!/bin/sh
#
# This is the script you need to provide to launch a redis instance
# and and service
#
kubectl create deployment redis-server-lab7 --image=redis
kubectl expose deployment redis-server-lab7 --port=6379
