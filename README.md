# FuzzStorm  

**FuzzStorm** is a high-performance, Burp Intruder-like fuzzing tool for testing web applications. It supports multiple attack modes, customizable payload injection, and response filtering based on status codes and content length.  

## Features  
- **Supports multiple attack modes**:  
  - **Sniper** (single-position fuzzing)  
  - **Battering Ram** (same payload at multiple positions)  
  - **Pitchfork** (parallel payload injection with multiple wordlists)  
  - **Cluster Bomb** (combinatorial payload injection)  
- **Parses raw HTTP requests** for dynamic fuzzing  
- **Multi-threaded execution** for high performance  
- **Customizable response filtering** by status codes and response lengths  
- **Wordlist-based fuzzing** with support for multiple wordlists  

## Installation  
Ensure you have Python 3 installed, then install the required dependencies:  
```sh
pip install requests
```

## Usage  
```sh
python fuzzstorm.py -r <request.txt> -w <wordlist.txt> -a <attack_type> -p <payload_marker(s)> [options]
```

### Required Arguments  
- `-r, --request <file>`: Path to the raw HTTP request file  
- `-w, --wordlist <file(s)>`: Path(s) to one or more wordlist files  
- `-a, --attack <type>`: Attack type (`sniper`, `battering_ram`, `pitchfork`, `cluster_bomb`)  
- `-p, --position <marker(s)>`: One or more payload position markers (e.g., `§1§`, `§2§`)  

### Optional Filters  
- `-s, --status <code(s)>`: Filter by HTTP status codes (e.g., `200`, `302`)  
- `-l, --length <min max>`: Filter by response length range (e.g., `500 2000`)  

## Attack Modes  
1. **Sniper**: Replaces a single position with each payload sequentially  
   ```sh
   python fuzzstorm.py -r request.txt -w wordlist.txt -a sniper -p §1§ -s 200 302
   ```
2. **Battering Ram**: Uses the same payload across multiple positions  
   ```sh
   python fuzzstorm.py -r request.txt -w wordlist.txt -a battering_ram -p §1§ §2§ -l 1000 5000
   ```
3. **Pitchfork**: Uses multiple wordlists for parallel fuzzing  
   ```sh
   python fuzzstorm.py -r request.txt -w wordlist1.txt wordlist2.txt -a pitchfork -p §1§ §2§ -s 200 -l 500 2000
   ```
4. **Cluster Bomb**: Tests all possible payload combinations  
   ```sh
   python fuzzstorm.py -r request.txt -w wordlist1.txt wordlist2.txt wordlist3.txt -a cluster_bomb -p §1§ §2§ §3§
   ```

## Example Output  
```
Payloads: ['admin'], Status: 200, Length: 1345, Time: 0.32s  
Payloads: ['guest'], Status: 403, Length: 532, Time: 0.29s  
Payloads: ['root'], Request failed  
```

## Notes  
- Ensure your raw request file includes placeholders (e.g., `§1§`) at positions you want to fuzz  
- The number of wordlists should match the number of payload positions for `pitchfork` and `cluster_bomb` attacks  
- The tool uses **10 concurrent threads** for better performance  

## License  
This project is released under the MIT License.  
