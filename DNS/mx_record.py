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
        print(response)
        # Parse the response based on record type
        if record_type == 15:  # MX record
            mx_records = []
            idx = 12  # Start parsing the response after the header
            while idx < len(response):
                priority, = struct.unpack("!H", response[idx:idx + 2])
                idx += 2
                mx_domain_len = response[idx]
                idx += 1
                mx_domain = response[idx:idx + mx_domain_len].decode("utf-8")
                idx += mx_domain_len
                mx_records.append((priority, mx_domain))
            return {"domain": domain, "mx_records": mx_records}
        else:
            return {"error": "Unsupported record type"}


    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example usage:
domain_to_query = "example.com"
mx_result = custom_dns_query(domain_to_query, 15)  # 15 corresponds to MX record type

print("MX Records:")
for priority, mail_exchange in mx_result["mx_records"]:
    print(f"Priority: {priority}, Mail Exchange: {mail_exchange}")
