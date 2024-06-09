import os
import tqdm
from scapy.packet import Raw


def recursive_file_gen(mydir):
    with open('../all_files_after.txt', 'w', encoding="utf-8") as f:
        for root, dirs, files in tqdm.tqdm(os.walk(mydir)):
            for file in files:
                base, ext = os.path.splitext(file)

                print(str(f'{os.path.join(root, file)}\n'))
                f.write(str(f'{os.path.join(root, file)}\n'))

#recursive_file_gen("C:\\Users\\Stepan\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache\\Cache_Data")

import os
import time
from scapy.all import sniff
from scapy.layers.http import HTTPRequest

from scapy.all import sniff
from scapy.layers.http import HTTPRequest, HTTPResponse


def extract_file_info(packet):
    if packet.haslayer(HTTPRequest):
        http_layer = packet[HTTPRequest]
        method = http_layer.Method.decode()
        host = http_layer.Host.decode() if http_layer.Host else "Unknown"
        path = http_layer.Path.decode() if http_layer.Path else "Unknown"

        print(f"HTTP request: {method} {host}{path}")

        if packet.haslayer(Raw):
            payload = packet[Raw].load
            headers = payload.decode(errors='ignore').split('\r\n')
            for header in headers:
                if "Content-Disposition" in header or "Content-Type" in header:
                    print(header)

    elif packet.haslayer(HTTPResponse):
        http_layer = packet[HTTPResponse]
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            headers = payload.decode(errors='ignore').split('\r\n')
            for header in headers:
                if "Content-Disposition" in header or "Content-Type" in header:
                    print(header)


# Фильтр для захвата HTTP трафика (TCP порт 80)
sniff(filter="tcp port 80", prn=extract_file_info, store=False)