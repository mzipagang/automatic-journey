# Get environment from developer
read -r -p "Enter environment (plg,dev,tst,stg,prd): " env
read -r -p "Enter City (Cincinnati,Chicago,Portland): " city
read -r -p "Enter State (OH,IL,OR): " state
read -r -p "Enter Operational Unit: " op_unit
CLIENT_ID="e451-api-$env-client-cert"
CLIENT_SERIAL=1

###### (instrux in the CA section above) ######
# rsa
openssl genrsa -aes256 -out "${CLIENT_ID}.pass.key" 2048
openssl rsa -in ${CLIENT_ID}.pass.key -out "${CLIENT_ID}.key"
rm "${CLIENT_ID}.pass.key"

# you should now have a `client.key` file.

# generate the CSR
openssl req -new -sha256 -key "${CLIENT_ID}.key" -subj "/C=US/ST=${state}/L=${city}/O=8451/OU=${op_unit}/CN=8451.cloud" -out "${CLIENT_ID}.csr"

# issue this certificate, signed by the CA root we made in the previous section
openssl x509 -req -sha256 -days 365 -in "${CLIENT_ID}.csr" -CA ca.pem -CAkey ca.key -set_serial ${CLIENT_SERIAL} -out "${CLIENT_ID}.pem"
cat "${CLIENT_ID}.key" "${CLIENT_ID}.pem ca.pem" > "${CLIENT_ID}.full.pem"
openssl pkcs12 -export -out "${CLIENT_ID}.full.pfx" -inkey "${CLIENT_ID}.key" -in "${CLIENT_ID}.pem" -certfile ca.pem

# Azure Key Vault requires a combined private key and certificate to import
openssl pkey -in ca.key -out ca.private.key
cat ca.pem ca.private.key > ca.azure.pem

certUpload() {
  read -r -p "Enter a name for your certificate in Key Vault (Ex: cert-name): " cert_name
  # Validate for correct KeyVault name format
  regex='^[0-9a-zA-Z-]+$'
  if [[ ${cert_name} =~ $regex ]]
  then
    az keyvault certificate import --vault-name "$1" -n "${cert_name}" -f "./ca.azure.pem" \
      -p "$(az keyvault certificate get-default-policy)"
  else
    echo "Invalid certificate name. Names may only have numbers, letters, and dashes."
    certUpload "$1"
  fi
}

secretUpload() {
  read -r -p "Enter a name for your CA secret in Key Vault (Ex: secret-name): " secret_name
  # Validate for correct KeyVault name format
  regex='^[0-9a-zA-Z-]+$'
  if [[ ${secret_name} =~ $regex ]]
  then
    az keyvault secret set --vault-name "$1" --name "${secret_name}" --file "ca.pem"
  else
    echo "Invalid secret name. Names may only have numbers, letters, and dashes."
    secretUpload "$1"
  fi
}

echo "Now uploading cert to Azure Key Vault..."
echo "Login to your 84.51º Azure Account"
az login

read -r -p "Enter Azure Keyvault name (Ex: kv-8451-apirefarch-dev): " kv_name
certUpload "${kv_name}"
secretUpload "${kv_name}"

echo "If there is no error above, the operations have completed successfully."