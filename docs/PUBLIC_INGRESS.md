# Using Public Ingress

## What is a Public Ingress?
Firstly, you should know what an ingress in Kubernetes is. Resources can be found at https://kubernetes.io/docs/concepts/services-networking/ingress/.

A public ingress utilizes [mTLS](https://www.cloudflare.com/learning/access-management/what-is-mutual-tls/) and OAuth2 to secure your API.
This is the currently agreed upon way to expose an API publicly at 84.51ª.

By contrast, internal ingresses utilize a firewall and OAuth2, only allowing Kroger on-prem + 84.51º services to access your API.

mTLS requires a certificate to be stored in your KeyVault to work. You must give any users of your API a client cert signed by the server cert stored in your KeyVault before they can access your API.

## Setup
You'll want to run `./init_project.sh` and answer `True` to the `enable_public_ingress` prompt.

To simplify the setting up of certs for your application, this template provides scripts that create and upload certs.

These scripts and their documentation can be found in the [scripts](../scripts) directory with instructions [here](../scripts/INSTRUCTIONS.md).

Afterwards, you should have a cert saved in your keychain. Go to your domain specified in your helm values with the _aks-ur-plg.8451.cloud_ domain.

If using Chrome, your browser should ask you to select a certificate for your site. Select your cert and click "ok". It should now ask you to login through Azure with your 84.51ª credentials.

If you see your front page, you have successfully set up your public ingress!
