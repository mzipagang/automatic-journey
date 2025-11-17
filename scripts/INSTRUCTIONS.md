# Instructions for these scripts
1. Run ```chmod +x ./gen_ca``` and ```chmod +x ./gen_client_cert.sh```
2. ```./gen_ca.sh```: Follow instructions given
3. ```./gen_client_cert.sh```:
   1. Will not work without having run ```gen_ca.sh``` first
   2. Generates your client cert and uploads ca cert and key to Azure Key Vault
4. Go to your values.<env>.yaml files in your [helm chart](../helm/fastapi-internal-template) and go to akvSecretsSync, changing the objectName of the 
object with the key "**ca.crt**" to whatever name you gave for the CA secret in the KeyVault.
5. To save your certs to your machine so they can be used:
   1. On Mac:
      1. Double click ```e451-api-<env>-client-cert.full.pfx``` and type the password you chose while running the scripts