# Generate an RSA key
openssl genrsa -aes256 -out ca.pass.key 2048
openssl rsa -in ca.pass.key -out ca.key
rm ca.pass.key

# You should now have a `ca.key` file.

# now generate the CA root cert
# when prompted, use whatever you'd like, but i'd recommend some human-readable Organization
# and Common Name.  I think the Common Name needs to match the DNS name of your API (but maybe not)
openssl req -new -x509 -sha256 -days 3650 -key ca.key -out ca.pem