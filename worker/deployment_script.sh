#Takes name of remote repo/image to use. eg.
#./deployment_script.sh gcr.io/csci5253/worker-server:v5

docker build . -t $1
docker push $1
#daemon pod for gpu drivers
kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/k8s-1.9/nvidia-driver-installer/cos/daemonset-preloaded.yaml

kubectl create -f worker-pod.yaml
kubectl set image -f worker-pod.yaml worker-server=$1
#create pod autoscaler
kubectl create -f hpa.yaml
