# PrivacyService

This project is used to demonstrate privacy-respecting services that can be under the control of an adversary.

This project is for demonstration purposes only and not tuned for performance.

## Prerequesites

- Python 3.5

### Generating a Self-signed Certificate

Assuming the domain for your server, where the P-Service is hosted, is `services.app-pets.org`:

```sh
cd PrivacyService
mkdir certs
cd certs
openssl genrsa -out services.app-pets.org.key 2048
openssl req -new -x509 -sha256 -key services.app-pets.org.key -out services.app-pets.org.crt -days 365 -subj /CN=services.app-pets.org
cd ..
ln -s certs/services.app-pets.org.key key.pem
ln -s certs/services.app-pets.org crt.pem
```

Changing the certificates require you to restart the P-Service.

### Trusting Self-signed Certificates

Note that you need to trust the certificate as it is self-signed and not signed by a trusted root Certificate Authority (CA).

#### macOS

You can either trust the certificate by opening it with the Keychain Accessapplication (which is the default for that file type) or by running the following command:

```sh
security add-trusted-cert -p ssl services.app-pets.org.crt
```

#### iOS

Get the `services.app-pets.org.crt` file onto the device or simulator and open it. The Settings application will guide you through the steps to install the certificate (which is called "Profile" there).

## API

Assuming the hostname is `services.app-pets.org`. Manual testing can be done with the following command:

```sh
openssl s_client -connect services.app-pets.org:<port>
```

### Key-value Storage

The Key-value storage can be used to store and retrieve values for given keys. The keys are 512 bit hexadecimal encoded strings consisting of 128 characters. The value is handled as binary.

 There is no user authentication or data protection, so anyone knowing a key can do retrieve or overwrite its value. Overwriting is done, by uploading data for an existing key. The previous value stored for that key is then lost.

Additionally, there is neither detection nor prevention of uploading non-encrypted data.

The entry point for the API is:

```
https://services.app-pets.org.test/storage/v1/<key>
```

To upload data use `POST` and attach the asset in binary format to the HTTP body of the request. To download data use `GET` and the value will be attached in binary form to the HTTP body of the response.

#### Upload

##### Request

```http
POST /storage/v1/<key> HTTP/1.1
Host: services.app-pets.org
Content-Type: application/octet-stream
Content-Length: <content.length>

<content>
```

##### Response

```http
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.5.2
Date: Tue, 06 Dec 2016 13:02:27 GMT
```

#### Download

##### Request

```http
GET /storage/v1/<key> HTTP/1.1
Host: services.app-pets.org
```

##### Response

```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: <content.length>

<content>
```

