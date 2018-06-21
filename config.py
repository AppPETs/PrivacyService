"""PrivacyService configuration module"""

DATABASES = {
    'TESTING': {
        'ENGINE': 'sqlite',
        'DATABASE_FILE': 'data.db' # Relative filepath!
    },
    'PRODUCTION' : {
        # Only sqlite and postgresql supported thus far.
        'ENGINE': 'postgresql',
        'NAME': '#DATABASE_NAME#',
        'USER': '#DATABASE_USER#',
        'ADDRESS': '#DATABASE_ADDRESS#',
        'PASSWORD': '#DATABASE_PASSWORD#'
    }
}

# Change for production
DATABASE = DATABASES['TESTING']

KEY_SIZE_IN_BITS = 256

# Only used when manually invoking the program using
# python3 pservice.py. Otherwise, gunicorn has to be
# configured manually
SERVER_CONFIGURATION = {
    'ADDRESS': '127.0.0.1',
    'PORT': 8080
}

SUPERFLUOUS_HEADERS_ALLOWED = True
REQUEST_LOGGING = True

# Hash size in bytes used to identify duplicates. For practical reasons,
# 80 bits should suffice!
DIGEST_SIZE = 10