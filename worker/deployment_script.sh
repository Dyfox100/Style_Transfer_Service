docker build . -t gcr.io/csci5253/worker-server:v3
docker push gcr.io/csci5253/worker-server:v3
#use below to install device drivers.
#kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/k8s-1.9/nvidia-driver-installer/cos/daemonset-preloaded.yaml
kubectl create -f worker-pod.yaml
