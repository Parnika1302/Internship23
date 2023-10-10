from fastapi import FastAPI
import dns.resolver
import dns.rdatatype
import whois

app = FastAPI()

def get_domain_age(domain):
    try:
        domain_info = whois.whois(domain)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        return creation_date
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def get_dmarc_record(domain):
    try:
        dmarc_domain = f'_dmarc.{domain}'
        txt_records = dns.resolver.query(dmarc_domain, 'TXT')
        
        dmarc_records = []
        for txt_record in txt_records:
            for txt_string in txt_record.strings:
                dmarc_records.append(txt_string)
        
        if dmarc_records:
            return dmarc_records
        else:
            return "No DMARC record found for the domain."

    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.get("/name-servers/")
async def get_name_servers(domain: str):
    try:
        ns_records = dns.resolver.query(domain, 'NS')

        ns_records_info = [ns.target.to_text() for ns in ns_records]

        return {"domain": domain, "name_servers": ns_records_info}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/mx-records/")
async def get_mx_records(domain: str):
    try:
        mx_records = dns.resolver.query(domain, 'MX')
        

        mx_records_info = [
            {
                "priority": mx.preference,
                "mail_server": mx.exchange.to_text()
            }
            for mx in mx_records
        ]     
        return {"domain": domain, "mx_records": mx_records_info}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


@app.get("/dmarc")
async def get_dmarc(domain:str):

    dmarc_records = get_dmarc_record(domain)

    return{"dmarc_records": dmarc_records}


@app.get("/a-record")
async def get_a_record(domain:str):

    a_records = dns.resolver.query(domain, 'A')

    a_records_info = [
            {
                "ip_address": ipval.to_text()
            }
            for ipval in a_records
        ]
    return{"a_record": a_records_info}


@app.get("/spf-records/")
async def get_spf_records(domain: str):
    try:
        # Perform a DNS TXT record query for SPF
        txt_records = dns.resolver.query(domain, 'TXT')
        
        # Extract and format the SPF records
        spf_records_info = []
        for txt_record in txt_records:
            for txt_string in txt_record.strings:
                if txt_string.startswith(b"v=spf1 "):  # Encode the string as bytes
                    spf_records_info.append(txt_string.decode())  # Decode the bytes to a string
        
        if spf_records_info:
            return {"domain": domain, "spf_records": spf_records_info}
        else:
            return {"domain": domain, "spf_records": "No SPF record found for the domain."}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/age")
async def get_age(domain:str):
    age=get_domain_age(domain)

    return {"domain": domain, "domain_age": age}


