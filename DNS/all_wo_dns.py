import whois
import socket
import struct

def custom_dns_query(domain, record_type):
    try:
        # DNS server (Google Public DNS)
        dns_server = "8.8.8.8"
        dns_port = 53
        
        # Create a UDP socket for DNS queries
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Build the DNS query packet
        query_id = 12345
        flags = 0b0000000100000000  # Standard query with recursion
        questions = 1
        answers = 0
        authority_rrs = 0
        additional_rrs = 0
        
        # DNS header
        dns_header = struct.pack("!HHHHHHH", query_id, flags, questions, answers, authority_rrs, additional_rrs, 0)
        
        # Encode the domain name
        domain_parts = domain.split(".")
        dns_question = b"".join(struct.pack("B", len(label)) + label.encode("utf-8") for label in domain_parts)
        dns_question += b"\x00"  # Null-terminated
        
        # DNS question section
        dns_question += struct.pack("!HH", record_type, 1)  # Record type (A, MX, or SPF) and class (IN)
        
        # Combine header and question to create the DNS query packet
        dns_query_packet = dns_header + dns_question
        
        # Send the query to the DNS server
        udp_socket.sendto(dns_query_packet, (dns_server, dns_port))
        
        # Receive the DNS response
        response, _ = udp_socket.recvfrom(1024)

        # Debugging: Print the DNS response
        print(response)
        
        # Parse the response based on record type
        if record_type == 1:  # A record
            ipv4_address = socket.inet_ntoa(response[-4:])
            return {"domain": domain, "a_records": [ipv4_address]}
        elif record_type == 15:  # MX record
            mx_records = []
            idx = 12  # Start parsing the response after the header
            while idx < len(response):
                priority, = struct.unpack("!H", response[idx:idx + 2])
                idx += 2
                mx_domain = response[idx:].split(b"\x00", 1)[0].decode("utf-8")
                mx_records.append(f"{priority} {mx_domain}")
                idx += len(mx_domain) + 1
            return {"domain": domain, "mx_records": mx_records}
        elif record_type == 99:  # SPF record (TXT record)
            spf_records = []
            # Search for TXT records (record type 16)
            idx = 12  # Start parsing the response after the header
            while idx < len(response):
                record_type, record_data_len = struct.unpack("!HH", response[idx:idx + 4])
                idx += 4
                if record_type == 16:  # TXT record
                    txt_data = response[idx:idx + record_data_len].decode("utf-8")
                    if txt_data.startswith("v=spf1"):
                        spf_records.append(txt_data)
                idx += record_data_len

            # Debugging: Print SPF records
            print(spf_records)

            return {"domain": domain, "spf_records": spf_records}
        else:
            return {"error": "Unsupported record type"}

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


# def custom_dns_query(domain, record_type):
#     try:
#         # DNS server (Google Public DNS)
#         dns_server = "8.8.8.8"
#         dns_port = 53
        
#         # Create a UDP socket for DNS queries
#         udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
#         # Build the DNS query packet
#         query_id = 12345
#         flags = 0b0000000100000000  # Standard query with recursion
#         questions = 1
#         answers = 0
#         authority_rrs = 0
#         additional_rrs = 0
        
#         # DNS header
#         dns_header = struct.pack("!HHHHHHH", query_id, flags, questions, answers, authority_rrs, additional_rrs, 0)
        
#         # Encode the domain name
#         domain_parts = domain.split(".")
#         dns_question = b"".join(struct.pack("B", len(label)) + label.encode("utf-8") for label in domain_parts)
#         dns_question += b"\x00"  # Null-terminated
        
#         # DNS question section
#         dns_question += struct.pack("!HH", record_type, 1)  # Record type (A, MX, or SPF) and class (IN)
        
#         # Combine header and question to create the DNS query packet
#         dns_query_packet = dns_header + dns_question
        
#         # Send the query to the DNS server
#         udp_socket.sendto(dns_query_packet, (dns_server, dns_port))
        
#         # Receive the DNS response
#         response, _ = udp_socket.recvfrom(1024)
        
#         # Parse the response based on record type
#         if record_type == 1:  # A record
#             ipv4_address = socket.inet_ntoa(response[-4:])
#             return {"domain": domain, "a_records": [ipv4_address]}
#         elif record_type == 15:  # MX record
#             mx_records = []
#             idx = 12  # Start parsing the response after the header
#             while idx < len(response):
#                 priority, = struct.unpack("!H", response[idx:idx + 2])
#                 idx += 2
#                 mx_domain = response[idx:].split(b"\x00", 1)[0].decode("utf-8")
#                 mx_records.append(f"{priority} {mx_domain}")
#                 idx += len(mx_domain) + 1
#             return {"domain": domain, "mx_records": mx_records}
#         elif record_type == 99:  # SPF record (TXT record)
#              spf_records = []
#             # Search for TXT records (record type 16)
#              idx = 12  # Start parsing the response after the header
#              while idx < len(response):
#                 record_type, record_data_len = struct.unpack("!HH", response[idx:idx + 4])
#                 idx += 4
#                 if record_type == 16:  # TXT record
#                     txt_data = response[idx:idx + record_data_len].decode("utf-8")
#                     if txt_data.startswith("v=spf1"):
#                         spf_records.append(txt_data)
#                 idx += record_data_len
#              return {"domain": domain, "spf_records": spf_records}
#         else:
#             return {"error": "Unsupported record type"}

#     except Exception as e:
#         return {"error": f"An error occurred: {str(e)}"}


def get_creation_date(domain):
    try:
        # Use the python-whois library to query and parse WHOIS data
        domain_info = whois.whois(domain)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        return {"domain": domain, "creation_date": creation_date}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example usage:
domain_to_query = "example.com"
a_result = custom_dns_query(domain_to_query, 1)  # 1 corresponds to A record type
mx_result = custom_dns_query(domain_to_query, 15)  # 15 corresponds to MX record type
spf_result = custom_dns_query(domain_to_query, 99)  # 99 corresponds to SPF record type
creation_date_result = get_creation_date(domain_to_query)


print("A Records:")
print(a_result)
print("MX Records:")
print(mx_result)
print("SPF Records:")
print(spf_result)
print("Creation Date:")
print(creation_date_result)




