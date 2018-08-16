# PrivacyService

This project is used to demonstrate privacy-respecting services that can be under the control of an adversary.

⚠️ If you use the demo service at [https://services.app-pets.org](https://services.app-pets.org/), **all requests are logged** in order to demonstrate the information collected by a potentially malicious service operator. Your IP address will be logged as well. **Do not use this in productive apps.** There is no guarantee of availability for data stored with the demo service.

## Prerequesites

- Python 3.6

### Python Libraries

- Bottle
- Gunicorn
- SQLAlchemy

The dependencies can be installed using

```sh
cd PrivacyService
# Setup virtualenv
virtualenv .
source bin/activate
pip3 install -r requirements.txt
```

## Documentation

### Setup and Installation

Project dependencies can be installed using `pip3`, as shown above. It is highly recommended to use a virtual environment to avoid cluttering the global namespace. Afterwards, the server can be invoked using either

```sh
# Invoke the server directly for local development only
python3 pservice.py
# or use gunicorn
gunicorn --workers=4 pservice:app
```

Note that the server port specified in the `conf.json` file is only used in the first case. When using `gunicorn`, gunicorn's default parameters are used instead.

The development server used by bottle itself adds the `Content-Length` and `Content-Type` request headers to all incoming requests, clashing with superfluous header detection. Gunicorn does not do this; The easiest solution is to temporarily turn off superfluous header detection for local development.

Per the [gunicorn documentation](http://docs.gunicorn.org/en/stable/deploy.html), it is highly recommended to run gunicorn behind a proxy server such as nginx, otherwise it is trivial to launch denial-of-service attacks against the service. This is also where it is appropriate to add TLS support. The underlying application does not need to handle encryption and decryption in this case. A full guide on how to setup the server using `nginx` remains to be done.

### Configuration

The server can be configured by editing a simple JSON file called `conf.json`, which is automatically generated on first run.

### HTTP Header Fingerprinting Protection

If a request contains superfluous HTTP headers, that is headers that are not required to answer the request, the request will be denied by default by replying with HTTP `400` (Bad Request). This is done in order to prevent fingerprinting attacks. Clients that send superfluous headers cannot use the service and a service can be tested if it accepts superfluous HTTP headers.

This behaviour can be disabled by setting the `SUPERFLUOUS_HEADERS_ALLOWED` preference in the `conf.json` file. Note that bottle's development server adds request headers to incoming requests (see above).

### Error Handling

If an API endpoint is invalid, e.g., because a specified key for the key-value storage API has an invalid format, the service will reply with `404` (Not Found).

If values in the request have an unexpected format, e.g., if a non-numerical value is used for the `Content-Length` header, the service will reply with `400` (Bad Request). This will also be replied if the request contains superfluous HTTP headers and `SUPERFLUOUS_HEADERS_ALLOWED` was not set.

### Request Logging

It is possible to configure the application to log all incoming requests, including the type of access (Retrieve, Update, Delete), the key used, the full HTTP request and values before and after the requested action. Logging is enabled using the `REQUEST_LOGGING` key in `conf.json`. This functionality can be used to study what information attackers might obtain from a mis-configured system.

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