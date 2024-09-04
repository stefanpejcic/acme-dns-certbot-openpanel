#!/usr/bin/env python3
import json
import os
import sys

# Path to the DNS zone files
ZONE_PATH_TEMPLATE = "/etc/bind/zones/{domain}.zone"
# Force re-registration. Overwrites the already existing DNS records.
FORCE_REGISTER = True

DOMAIN = os.environ["CERTBOT_DOMAIN"]
if DOMAIN.startswith("*."):
    DOMAIN = DOMAIN[2:]
VALIDATION_DOMAIN = "_acme-challenge." + DOMAIN
VALIDATION_TOKEN = os.environ["CERTBOT_VALIDATION"]

class ZoneFileManager(object):
    """
    Handles the manipulation of the local BIND DNS zone files
    """

    def __init__(self, domain):
        self.zonefile = ZONE_PATH_TEMPLATE.format(domain=domain)
        self.domain = domain
        self.load_zone_file()

    def load_zone_file(self):
        """Reads the DNS zone file into memory"""
        try:
            with open(self.zonefile, 'r') as fh:
                self.lines = fh.readlines()
        except IOError:
            print(f"ERROR: Could not read zone file {self.zonefile}")
            sys.exit(1)

    def save_zone_file(self):
        """Writes the DNS zone file back to disk"""
        try:
            with open(self.zonefile, 'w') as fh:
                fh.writelines(self.lines)
        except IOError:
            print(f"ERROR: Could not write to zone file {self.zonefile}")
            sys.exit(1)

    def update_txt_record(self, validation_domain, validation_token):
        """Updates or adds the TXT record in the zone file"""
        # Remove any existing TXT record for this validation domain
        self.lines = [line for line in self.lines if not line.startswith(validation_domain + " ")]

        # Add the new TXT record
        new_record = f'{validation_domain}. IN TXT "{validation_token}"\n'
        self.lines.append(new_record)

        # Increment the zone serial number
        self.increment_serial()

        # Save the updated zone file
        self.save_zone_file()

        # Reload the BIND server to apply changes
        #self.reload_bind() # inotify instead

    def increment_serial(self):
        """Increments the serial number in the zone file"""
        # match the dns zone template for bind9 running on openpanel
        # https://github.com/stefanpejcic/openpanel-configuration/blob/cdd08aacd287956dc51ce4c34dfdfaf2669a1468/bind9/zone_template.txt#L3
        for i, line in enumerate(self.lines):
            if "SOA" in line:
                serial_idx = i + 1
                break
        else:
            print("ERROR: SOA record not found in zone file.")
            sys.exit(1)

        # Extract the serial number from the identified line
        serial_line = self.lines[serial_idx].strip()
        serial_number = int(serial_line.split()[0])

        # Increment the serial number
        new_serial = serial_number + 1

        # Replace the old serial with the new one, preserving the comment
        self.lines[serial_idx] = f"                        {new_serial}      ; Serial number\n"


    def reload_bind(self):
        """Reloads the BIND container to apply changes"""
        ret = os.system(f"docker exec openpanel_dns rndc reload {DOMAIN}")
        if ret != 0:
            print("ERROR: Failed to reload BIND server.")
            sys.exit(1)


if __name__ == "__main__":
    # Init
    zone_manager = ZoneFileManager(DOMAIN)

    # Update the TXT record in the local zone file
    zone_manager.update_txt_record(VALIDATION_DOMAIN, VALIDATION_TOKEN)
