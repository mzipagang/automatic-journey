#!/bin/zsh

e='\033'
RESET="${e}[0m"
CYAN="${e}[0;96m"
RED="${e}[0;91m"
GREEN="${e}[0;92m"

info() {
  echo -e "${CYAN}${*}${RESET}"
}

error() {
  echo -e "${RED}${*}${RESET}"
}

success() {
  echo -e "${GREEN}${*}${RESET}"
}

_exists() {
  command -v "$1" >/dev/null 2>&1
}

local subscription=$1
local resourceGroup=$2
local cluster=$3
local namespace=$4

if [ -z $subscription ]; then
  error "Please provide a subscription"
  return
fi

if [ -z $resourceGroup ]; then
  error "Please provide a resource group"
  return
fi

if [ -z $cluster ]; then
  error "Please provide a cluster"
  return
fi

if [ -z $namespace ]; then
  error "Please provide a namespace"
  return
fi

info "Logging into cluster: $cluster and namespace: $namespace"
command az logout
command az login
command az account set --subscription "$subscription"
# Playground Cluster
command az aks get-credentials --resource-group $resourceGroup --name $cluster
command kubectl config set-context --current --namespace=$namespace

if _exists kubelogin && [[ -f "$KUBECONFIG" ]]; then
  command kubelogin convert-kubeconfig
fi

success "Successfully logged into cluster: $cluster and namespace: $namespace"