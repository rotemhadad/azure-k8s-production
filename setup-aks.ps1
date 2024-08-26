# setup-aks.ps1

param (
    [string]$resourceGroupName = "K8S-Cluster-Rotem",
    [string]$aksClusterName = "RotemCluster001",
    [string]$location = "Israel Central",
)

# Install Azure CLI if not installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Azure CLI not found. Installing Azure CLI..."
    Invoke-WebRequest -Uri "https://aka.ms/installazurecliwindows" -OutFile "AzureCLI.msi"
    Start-Process msiexec.exe -ArgumentList '/I AzureCLI.msi /quiet' -NoNewWindow -Wait
}

# Log in to Azure
az login

# Create Resource Group
az group create --name $resourceGroupName --location $location

# Create AKS Cluster
az aks create `
    --resource-group $resourceGroupName `
    --name $aksClusterName `
    --node-count 1 `
    --enable-addons monitoring `
    --enable-rbac `
    --location $location `
    --generate-ssh-keys

# Get AKS credentials
az aks get-credentials --resource-group $resourceGroupName --name $aksClusterName

# Deploy NGINX Ingress Controller & Wait for Ingress controller to be fully deployed
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
Start-Sleep -Seconds 60

# Apply custom Ingress configuration and default backend
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/nginx-default.yaml
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/ingress.yaml

# Deploy Network Policy
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/network-policy-deny-a-to-b.yaml

# Deploy Services
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/service-a.yaml
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/service-b.yaml
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/service-a-service.yaml
kubectl apply -f https://raw.githubusercontent.com/rotemhadad/azure-k8s-production/master/service-b-service.yaml

# Wait for services to be up and running
Start-Sleep -Seconds 30

# Check the status of the services
kubectl get pods
kubectl get services
kubectl get ingress

Write-Host "Deployment completed. Check the status of your services and ingress."

# Output useful URLs
$ingressIP = kubectl get services -o jsonpath="{.items[?(@.metadata.name=='ingress-nginx-controller')].status.loadBalancer.ingress[0].ip}"
Write-Host "Access Service A at http://$ingressIP/service-A"
Write-Host "Access Service B at http://$ingressIP/service-B"

