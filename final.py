import ipaddress
import publicsuffix2 as psl
import random
import socket
import validators
from collections import defaultdict

QTYPE = {
    1: 'A',    
    2: 'NS',   
    5: 'CNAME', 
    12: 'PTR', 
    15: 'MX',  
    16: 'TXT', 
    28: 'AAAA',
    'A': 1,    
    'NS': 2,   
    'CNAME': 5, 
    'PTR': 12, 
    'MX': 15,  
    'TXT': 16, 
    'AAAA': 28
}

OPCODE = {
    0: 'Query',
    1: 'IQuery',
    2: 'Status',
    4: 'Notify',
    5: 'Update',
    6: 'DSO'
}

RCODE = {
    0: 'NoError',
    1: 'FormErr',
    2: 'ServFail',
    3: 'NXDomain',
    4: 'NotImp',
    5: 'Refused',
    6: 'YXDomain',
    7: 'YXRRSet',
    8: 'NXRRSet',
    9: 'NotAuth',
    10: 'NotZone',
    11: 'DSOTYPENI'
}

def byte2int(by: bytes) -> int:
    if not isinstance(by, bytes):
        raise TypeError()
    return int.from_bytes(by, 'big')

def byte2hex(by: bytes) -> str:
    if not isinstance(by, bytes):
        raise TypeError()
    return by.hex()

def dns_opcode(n: int):
    if not isinstance(n, int):
        raise TypeError()
    if n not in OPCODE:
        raise ValueError()
    return OPCODE[n]

def dns_rcode(n: int):
    if not isinstance(n, int):
        raise TypeError()
    if n not in RCODE:
        raise ValueError()
    return RCODE[n]

def dns_cd(n: int):
    if n not in (0, 1):
        raise ValueError()
    return ['Unacceptable', 'Acceptable'][n]

def dns_qclass(n: int):
    if n == 1:
        return 'INTERNET'
    else:
        raise ValueError('Invalid QCLASS value received')

DECODE_HEADER = [byte2hex, byte2hex, byte2int, byte2int, byte2int, byte2int]
FLAG_LENGTH = [1, 4, 1, 1, 1, 1, 1, 1, 1, 4]
HEADERS = ['ID', 'Flags', 'Questions', 'Answers', 'Authorative Answers', 'Additional Resources']

FLAGS = [
    'Response',
    'Operation Code',
    'Authoritative Answer',
    'Truncated',
    'Recursion Desired',
    'Recursion Available',
    'Reserved',
    'Authenticated Answer',
    'Non-authenticated Answer',
    'Error Code'
]

# SOA_NUMBERS = ['Serial Number', 'Refresh Interval', 'Retry Interval', 'Expire Limit', 'Minimum TTL']

DECODE_FLAG = [bool, dns_opcode, bool, bool, bool, bool, int, bool, dns_cd, dns_rcode]

def decode_flags(flag: str) -> dict:
    if not isinstance(flag, str):
        raise TypeError()
    if not (len(flag) == 4 and all(i in '0123456789abcdef' for i in flag)):
        raise ValueError()
    flag = '{:016b}'.format(int(flag, 16))
    index = 0
    flags = []
    for i, f in zip(FLAG_LENGTH, DECODE_FLAG):
        flags.append(f(int(flag[index:index+i], 2)))
        index += i
    return dict(zip(FLAGS, flags))

def decode_response(fields: bytes) -> dict:
    if not isinstance(fields, bytes):
        raise TypeError()
    if len(fields) != 10:
        raise ValueError()
    qtype = QTYPE[byte2int(fields[:2])]
    qclass = dns_qclass(byte2int(fields[2:4]))
    ttl = byte2int(fields[4:8])
    length = byte2int(fields[8:10])
    return {
        'QType': qtype,
        'QClass': qclass,
        'Time-to-live': ttl,
        'Data length': length
    }

def valid_domain(domain):
    return (validators.domain(domain) and psl.get_sld(domain, strict=True))

def make_query(query, qtype):
    if not (isinstance(query, str) and isinstance(qtype, str)):
        raise TypeError('Parameters must be instances of `str`')
    qtype = QTYPE.get(qtype.upper(), None)
    if not qtype:
        raise ValueError('QTYPE is invalid or unsupported')
    if qtype == 12:
        if validators.ipv4(query):
            query = ipaddress.IPv4Address(query).reverse_pointer
        elif validators.ipv6(query):
            query = ipaddress.IPv6Address(query).reverse_pointer
        else:
            raise ValueError('QUERY is not a valid IPv4 or IPv6 address')
    else:
        if not (validators.domain(query) and (sld := psl.get_sld(query, strict=True))):
            raise ValueError('QUERY is not a valid web domain')
        if qtype in (2, 15, 16):
            query = sld
    return b''.join([
        random.randbytes(2), b'\1\0\0\1\0\0\0\0\0\0',
        ''.join(chr(len(i)) + i for i in query.split('.')).encode('utf8'),
        b'\0', qtype.to_bytes(2, 'big'), b'\0\1'
    ])

class DNS_Parser:
    def __init__(self, response: bytes) -> None:
        if not isinstance(response, bytes):
            raise TypeError('Argument must be an instance of `bytes`')
        self.response = response
        self.names = dict()
        self.question = dict()
        self.answers = []
        # self.soa = []
        self.position = 0
        self.raw = dict()
        self.simple = dict()
    
    def check_bounds(self, pos: int):
        if not isinstance(pos, int):
            raise TypeError('Argument must be an instance of `int`')
        if pos >= len(self.response):
            raise IndexError('Index exceeds the maximum possible value')
    
    def read_stream(self, pos: int, recur: bool=False, length: int=0) -> str:
        self.check_bounds(pos)
        chunks = []
        count = 0
        while True:
            hint = self.response[pos]
            if hint == 0:
                if not recur:
                    self.position = pos
                break
            elif hint == 192:
                index = self.response[pos+1]
                self.position = pos+1
                if index in self.names:
                    name = self.names[index]
                else:
                    name = self.read_stream(index, True)
                    self.names[index] = name
                chunks.append(name)
                pos += 2
                count += 2
                if not length or count == length:
                    break
                else:
                    continue 
            pos += 1
            count += 1
            chunk = self.response[pos:pos+hint].decode('utf8')
            chunks.append(chunk)
            pos += hint
            count += hint
        return '.'.join(chunks)
    
    def parse_dns_query(self):
        pos = self.response[12:].index(0)
        query = self.response[:pos+17]
        headers = [f(query[:12][i:i+2]) for f, i in zip(DECODE_HEADER, range(0, 12, 2))]
        self.question = dict(zip(HEADERS, headers))
        flags = self.question['Flags']
        self.question['Flags'] = {
            'Hexadecimal': flags, 'Binary': f'{int(flags, 16):016b}',
            'Breakdown': decode_flags(flags)
        }
        name = self.read_stream(12)
        self.names[12] = name
        qtype = QTYPE[byte2int(query[pos+13:pos+15])]
        self.position = pos + 16
        self.question.update({
            'Name': name, 'Type': qtype,
            'Class': dns_qclass(byte2int(query[-2:]))
        })
    
    def rdata_ipv4(self, pos: int) -> str:
        self.check_bounds(pos+3)
        return '.'.join([str(i) for i in self.response[pos:pos+4]])
    
    def rdata_ipv6(self, pos: int) -> str:
        self.check_bounds(pos+15)
        return str(ipaddress.IPv6Address(self.response[pos:pos+16]))
    
    def rdata_txt(self, pos: int, length: int) -> dict:
        self.check_bounds(pos+length-1)
        return {'Text length': self.response[pos], 'Text': self.response[pos+1:pos+length+1].decode('utf8')}
    
    def rdata_mx(self, pos: int, length: int) -> dict:
        return {'Preference': byte2int(self.response[pos:pos+2]), 'Mail Exchange': self.read_stream(pos+2, length-2)}
    
    # def rdata_soa(self, pos: int) -> dict:
    #     pns = self.read_stream(pos)
    #     ramx = self.read_stream(self.position+1)
    #     fields = self.response[self.position+1:self.position+21]
    #     soa = [byte2int(fields[i:i+4]) for i in range(0, 20, 4)]
    #     soa = dict(zip(SOA_NUMBERS, soa))
    #     rdata = {'Primary Name Server': pns, "Responsible Authority's Mailbox": ramx}
    #     rdata.update(soa)
    #     self.position += 20
    #     return rdata
    
    def parse_dns_answer(self):
        qname = self.read_stream(self.position+1)
        headers = decode_response(self.response[self.position+1:self.position+11])
        answer = {'QName': qname}
        answer.update(headers)
        qtype = headers['QType']
        length = headers['Data length']
        if length == 0:
            raise ValueError('DNS message is malformed or invalid')
        if qtype == 'A':
            if length != 4:
                raise ValueError('DNS message is malformed or invalid')
            rdata = self.rdata_ipv4(self.position+11)
            self.position += 14
        elif qtype == 'AAAA':
            if length != 16:
                raise ValueError('DNS message is malformed or invalid')
            rdata = self.rdata_ipv6(self.position+11)
            self.position += 26
        elif qtype == 'TXT':
            rdata = self.rdata_txt(self.position+11, length)
            if length - rdata['Text length'] != 1:
                raise ValueError('DNS message is malformed or invalid')
            self.position += (10 + length)
        elif qtype in ('CNAME', 'NS', 'PTR'):
            rdata = self.read_stream(self.position+11, length)
            if not valid_domain(rdata):
                raise ValueError('DNS message is malformed or invalid')
        elif qtype == 'MX':
            if length == 3 and self.response[self.position+13] == 0:
                prefs = byte2int(self.response[self.position+11:self.position+13])
                rdata = {'Preference': prefs, 'Mail Exchange': '<Root>'}
                self.position += 13
            else:
                rdata = self.rdata_mx(self.position+11, length)
                mx = rdata['Mail Exchange']
                if not valid_domain(mx):
                    raise ValueError('DNS message is malformed or invalid')
        # elif qtype == 'SOA':
        #     rdata = self.rdata_soa(self.position+11)
        #     pns, ramx = rdata['Primary Name Server'], rdata["Responsible Authority's Mailbox"]
        #     if not (valid_domain(pns) and valid_domain(ramx)):
        #         raise ValueError('DNS message is malformed or invalid')
        answer['RData'] = rdata
        self.answers.append(answer) 
    
    def parse_dns_response(self):
        self.parse_dns_query()
        total = sum((
            self.question['Answers'], 
            self.question['Authorative Answers'],
            self.question['Additional Resources']
        ))
        count = 0
        while count < total:
            self.parse_dns_answer()
            count += 1
        self.raw['Question'] = self.question
        self.raw['Answers'] = self.answers
        
        # if self.soa:
        #     self.raw['Authorative Answers'] = self.soa

def dns_query(query, address, qtype):
    request = make_query(query, qtype)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.sendto(request, (address, 53))
        response = sock.recv(8192)
    except Exception as e:
        print(e)
        return
    finally:
        sock.close()
    parser = DNS_Parser(response)
    parser.parse_dns_response()
    
    if 'Question' in parser.raw:
        question = parser.raw['Question']
        print("QName:", question.get('Name', 'N/A'))
        print("QType:", question.get('Type', 'N/A'))
    
    if 'Answers' in parser.raw:
        for answer in parser.raw['Answers']:
            print("RData:", answer.get('RData', 'N/A'))
    
    if 'Authorative Answers' in parser.raw:
        for answer in parser.raw['Authorative Answers']:
            print("RData:", answer.get('RData', 'N/A'))

address = "8.8.8.8"
query = input("Domain name: ")  # Change this to the domain or IP address you want to query
qtype = input("Record Type: ")  # Change this to the desired query type

# Call the dns_query function
dns_query(query, address, qtype)
