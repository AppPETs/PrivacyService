# PrivacyService

This project is used to demonstrate privacy-respecting services that can be under the control of an adversary.

This project is for demonstration purposes only and not tuned for performance.

## Prerequesites

- Python 3.6

### Generating a Self-signed Certificate

⚠️ Only use self-signed certificates during development and testing, not for production.

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

⚠️ Only use self-signed certificates during development and testing, not for production.

Note that you need to trust the certificate as it is self-signed and not signed by a trusted Certificate Authority (CA).

#### macOS

You can either trust the certificate by opening it with the *Keychain Access* application (which is the default for that file type) or by running the following command:

```sh
security add-trusted-cert -p ssl certs/services.app-pets.org.crt
```

#### iOS

Get the `certs/services.app-pets.org.crt` file onto the device or simulator and open it. The *Settings* application will guide you through the steps to install the certificate (which is called "Profile" there).

Since iOS 10.3 in addition you need to go to *Settings* → *General* → *About* → *Certificate Trust Settings* and enable full trust for the root certificate you just added.

### Diagnostics

A quick test if a secure connection to the service can be established can be done with the following command:

```sh
openssl s_client -connect services.app-pets.org:<port>
```

On macOS you can check if the TLS setup is correct. This helps diagnosing if a connection can be established with the default App Transport Security (ATS) policy of iOS or macOS applications. If a self-signed certificate is used, this certificate has to be trusted as described in the previous section.

```sh
nscurl --ats-diagnostics https://services.app-pets.org:<port>
```

### Testing

In order to execute unit test, run the following command:

```sh
./pservice --test
```

## Documentation

### HTTP Header Fingerprinting Protection

If a request contains superfluous HTTP headers, that is headers that are not required to answer the request, the request will be denied by default by replying with HTTP `400` (Bad Request). This is done in order to prevent fingerprinting attacks. Clients that send superfluous headers cannot use the service and a service can be tested if it accepts superfluous HTTP headers.

This behaviour can be disabled with the `--allow-superfluous-headers` command line option.

### Test Vectors

In order to test clients against a real service the service can offer test vectors. Test vectors are specified in `test_vectors.json`. They are not enabled by default and can be enabled by passing the `--enable-test-vectors` command line option. 

An example request for getting a test vector for the key-value storage API can be issued with the following command:

```sh
curl 'https://services.app-pets.org/storage/v1/fcb6471961829d28270462a2d5cba7fd141d80c608d6df074f8e2e213c187471' --header 'User-Agent:' --header 'Accept:' --cacert 'crt.pem' --raw --silent | base64
```

This should print `IdW1+TjJj3KaW79XN1FaFRJoU2Y5T79IkI7zi/vGkh25lFRU2Of+/2mKR58=` to the terminal output.

### Error Handling

If an API endpoint is invalid, e.g., because a specified key for the key-value storage API has an invalid format, the service will reply with `404` (Not Found).

If values in the request have an unexpected format, e.g., if a non-numerical value is used for the `Content-Length` header, the service will reply with `400` (Bad Request). This will also be replied if the request contains superfluous HTTP headers and `--allow-superfluous-headers` was not set.

### Key-value Storage API

The Key-value storage can be used to store and retrieve values for given keys. The keys are 256 bit hexadecimal encoded strings consisting of 64 characters. The value is handled as binary.

There is no user authentication or data protection, so anyone knowing a key can do retrieve or overwrite its value. Overwriting is done by uploading data for an existing key. The previous value stored for that key is then lost.

Additionally, there is neither detection nor prevention of uploading non-encrypted data.

The entry point for the API is:

```
https://services.app-pets.org/storage/v1/<key>
```

To upload data use `POST` and attach the asset in binary format to the HTTP body of the request. To download data use `GET` and the value will be attached in binary form to the HTTP body of the response. To delete entries use the `DELETE` method.

#### Storing / Uploading

##### Request

If there already exists a value for `<key>` the previously stored value will be overwritten.

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
Server: BaseHTTP/0.6 Python/3.6.0
Date: Wed, 25 Jan 2017 13:00:00 GMT
```

#### Retrieving / Downloading

##### Request

```http
GET /storage/v1/<key> HTTP/1.1
Host: services.app-pets.org
```

##### Response

If no value exists for the given `<key>`, the service will reply with HTTP `404` (Not Found).

```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: <content.length>

<content>
```

#### Deleting

##### Request

```http
DELETE /storage/v1/<key> HTTP/1.1
Host: services.app-pets.org
```

##### Response

Regardless if the key is existing the response will be `200`. The response will only indicate an error if the request is erroneous, e.g., if `<key>` has an invalid format.

```http
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.6.0
Date: Wed, 25 Jan 2017 13:00:00 GMT
```