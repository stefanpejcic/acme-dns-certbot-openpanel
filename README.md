# acme-dns-certbot-joohoi

An example [Certbot](https://certbot.eff.org) client hook for [acme-dns](https://github.com/joohoi/acme-dns). 

This authentication hook automatically registers acme-dns accounts and on initial run automatically add the CNAME records to bind9 dns zone running in separate docker container. Subsequent automatic renewals by Certbot container run in the background non-interactively.

Requires Certbot >= 0.10, and Python3

## Usage

On initial run:
```
$ certbot certonly --manual --manual-auth-hook /etc/letsencrypt/acme-dns-auth.py \
   --preferred-challenges dns --debug-challenges                                 \
   -d example.org -d \*.example.org
```

Note that the `--debug-challenges` is mandatory here to pause the Certbot execution before asking Let's Encrypt to validate the records and let you to manually add the CNAME records to your main DNS zone.

After adding the prompted CNAME records to your zone(s), wait for a bit for the changes to propagate over the main DNS zone name servers. This takes anywhere from few seconds up to a few minutes, depending on the DNS service provider software and configuration. Hit enter to continue as prompted to ask Let's Encrypt to validate the records.

After the initial run, Certbot is able to automatically renew your certificates using the stored per-domain acme-dns credentials. 
