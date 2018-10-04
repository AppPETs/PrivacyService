/**
 * Copyright 2018 by Jakob Rieck.
 * Inspired and based on work by David Kerkeslager
 * see https://stackoverflow.com/a/1264046
 */
export let URIHash =
{
    /**
     * Load the contents of the URI hash into an object, where the key maps to the provided
     * value.
     */
    load : function()
    {
        // Split initial '#' symbols
        return document.location.hash.substring(1)
            // Separate individual items
            .split('&')
            // Separate keys and values
            .map(str => str.split('='))
            // Only process expected keys and values
            .filter(tuple => tuple.length == 2)
            // Build up object mapping keys to values
            .reduce(function(r, pair) {
                let key = pair[0], value = pair[1];

                r[decodeURI(key)] = decodeURI(value);
                return r;
            }, {});
    },

    /**
     * Takes an object to serialize and stores it in the URI hash.
     */
    store : function(obj)
    {
        let hash = Object.keys(obj)
                         // Encode key-value pair as string with = separator
                         .map(k => encodeURI(k) + '=' + encodeURI(obj[k]))
                         .join('&')

        document.location.hash = hash
    },

    /**
     * Get the value of a key from the hash.  If the hash does not contain the key or the hash is invalid,
     * the function returns undefined.
     */
    get: function(key)
    {
        return this.load()[key];
    },

    /**
     * Set the value of a key in the hash.  If the key does not exist, the key/value pair is added.
     */
    set: function(key, value)
    {
        var dump = this.load();
        dump[key] = value;
        this.store(dump)
    }
}