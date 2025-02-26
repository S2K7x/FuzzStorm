import requests
import argparse
from concurrent.futures import ThreadPoolExecutor
from itertools import product

def fuzz_request(url, method, headers, data, payload_positions, payloads):
    try:
        modified_url = url
        modified_data = data
        for position, payload in zip(payload_positions, payloads):
            modified_url = modified_url.replace(position, payload)
            modified_data = modified_data.replace(position, payload)

        if method.upper() == 'GET':
            response = requests.get(modified_url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=modified_data, timeout=10)
        else:
            return None, None, None

        return response.status_code, len(response.content), response.elapsed.total_seconds()

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None, None, None

def parse_raw_request(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            raw_request = f.read()

        lines = raw_request.split('\n')
        request_line = lines[0].strip()
        method, path, _ = request_line.split(' ', 2)

        host = next((line.split(': ')[1].strip() for line in lines if line.lower().startswith('host:')), None)
        if not host:
            raise ValueError("Host header not found in the raw request.")
        
        url = f"https://{host}{path}" if "https" in raw_request.lower() else f"http://{host}{path}"

        headers = {}
        header_lines = [line.strip() for line in lines[1:] if line.strip() and ':' in line]
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        data = ''
        if '\r\n\r\n' in raw_request:
            data = raw_request.split('\r\n\r\n', 1)[1].strip()
        elif '\n\n' in raw_request:
             data = raw_request.split('\n\n', 1)[1].strip()

        return url, method, headers, data

    except FileNotFoundError:
        print(f"Error: Raw request file '{filename}' not found.")
        return None, None, None, None
    except ValueError as e:
        print(f"Error parsing raw request: {e}")
        return None, None, None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None, None, None

def read_wordlist(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Error: Wordlist file '{filename}' not found.")
        return []

def generate_payloads(attack_type, payload_positions, wordlists):
    if attack_type == "sniper":
        for position in payload_positions:
            for payload in wordlists[0]:
                yield [position], [payload]
    elif attack_type == "battering_ram":
        for payload in wordlists[0]:
            yield payload_positions, [payload] * len(payload_positions)
    elif attack_type == "pitchfork":
        for payloads in zip(*wordlists):
            yield payload_positions, payloads
    elif attack_type == "cluster_bomb":
        for payloads in product(*wordlists):
            yield payload_positions, payloads

def main():
    parser = argparse.ArgumentParser(description="Multi-mode Burp Intruder-like fuzzing tool", 
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  1. Sniper attack with status code filter:
     python script_name.py -r request.txt -w wordlist.txt -a sniper -p §1§ -s 200 302

  2. Battering ram attack with response length filter:
     python script_name.py -r request.txt -w wordlist.txt -a battering_ram -p §1§ §2§ -l 1000 5000

  3. Pitchfork attack with both status and length filters:
     python script_name.py -r request.txt -w wordlist1.txt wordlist2.txt -a pitchfork -p §1§ §2§ -s 200 -l 500 2000

  4. Cluster bomb attack with three positions and three wordlists:
     python script_name.py -r request.txt -w wordlist1.txt wordlist2.txt wordlist3.txt -a cluster_bomb -p §1§ §2§ §3§

Note:
  - Ensure that the number of wordlists matches the number of payload positions for 'pitchfork' and 'cluster_bomb' attacks.
  - The raw request file should use the same payload position markers as specified in the -p argument.
  - The tool uses multi-threading to improve performance, with a default of 10 concurrent requests.
  - Use -s or --status to filter by specific status code(s)
  - Use -l or --length to filter by response length range (min max)
  - Filters can be combined for more precise results
""")
    parser.add_argument("-r", "--request", required=True, help="Path to the raw HTTP request file.")
    parser.add_argument("-w", "--wordlist", required=True, nargs='+', help="Path(s) to one or more wordlist files.")
    parser.add_argument("-a", "--attack", required=True, choices=["sniper", "battering_ram", "pitchfork", "cluster_bomb"], 
                        help="Specify the attack type.")
    parser.add_argument("-p", "--position", required=True, nargs='+', help="Specify one or more payload position markers in the request.")
    parser.add_argument("-s", "--status", type=int, nargs='+', help="Filter results by specific status code(s)")
    parser.add_argument("-l", "--length", type=int, nargs=2, help="Filter results by response length range (min max)")
    args = parser.parse_args()

    url, method, headers, data = parse_raw_request(args.request)
    if url is None or method is None or headers is None:
        print("Failed to parse request. Exiting.")
        return

    wordlists = [read_wordlist(wl) for wl in args.wordlist]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for positions, payloads in generate_payloads(args.attack, args.position, wordlists):
            future = executor.submit(fuzz_request, url, method, headers, data, positions, payloads)
            futures.append((payloads, future))

        for payloads, future in futures:
            status_code, content_length, response_time = future.result()
            if status_code is not None:
                # Apply filters
                if args.status and status_code not in args.status:
                    continue
                if args.length and not (args.length[0] <= content_length <= args.length[1]):
                    continue
                
                print(f"Payloads: {payloads}, Status: {status_code}, Length: {content_length}, Time: {response_time:.2f}s")
            else:
                print(f"Payloads: {payloads}, Request failed")

if __name__ == "__main__":
    main()
