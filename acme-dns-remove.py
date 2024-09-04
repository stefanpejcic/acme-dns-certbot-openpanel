#!/usr/bin/env python3
import os
import sys
import time

# Path to the DNS zone files
ZONE_PATH_TEMPLATE = "/etc/bind/zones/{domain}.zone"

DOMAIN = os.environ["CERTBOT_DOMAIN"]
if DOMAIN.startswith("*."):
    DOMAIN = DOMAIN[2:]
VALIDATION_DOMAIN = "_acme-challenge." + DOMAIN

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
                time.sleep(5) # wait for propagation for next record
        except IOError:
            print(f"ERROR: Could not write to zone file {self.zonefile}")
            sys.exit(1)

    def delete_txt_record(self, validation_domain):
        """Deletes the TXT record from the zone file"""
        updated_lines = []
        
        for line in self.lines:
            # Check if the line starts with the validation domain
            if not line.startswith(f"{validation_domain}."):
                # Keep the line if it doesn't match the validation domain
                updated_lines.append(line)

        # Replace the old lines with the updated lines
        self.lines = updated_lines
    
        # Increment the zone serial number
        self.increment_serial()
    
        # Save the updated zone file
        self.save_zone_file()

    def increment_serial(self):
        """Increments the serial number in the zone file"""
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


if __name__ == "__main__":
    # Init
    zone_manager = ZoneFileManager(DOMAIN)

    # Delete the TXT record from the local zone file
    zone_manager.delete_txt_record(VALIDATION_DOMAIN)
