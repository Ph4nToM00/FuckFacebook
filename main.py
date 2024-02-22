import argparse
import requests
from bs4 import BeautifulSoup
from terminaltables import SingleTable
import sys
import time
from colorama import Fore, Style
import os
from static.banner import display_banner
import socks
import socket
from tqdm import tqdm

# Configure the socket to use Tor
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # 9050 est le port par défaut de Tor
socket.socket = socks.socksocket

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def save_results(data):
    if not data:
        print("No data to save.")
        return

    save = input("\nDo you want to save the results to a file? (y/n): ").lower()
    if save == 'y':
        filename = input("\nEnter filename to save results to: ")
        with open(filename, 'w') as file:
            for row in data:
                file.write(','.join(row) + '\n')
        print(f"Results saved to {filename}")

def get_terminal_width():
    """Get the current width of the terminal."""
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(columns)

def adjust_table_width(table_instance):
    """Adjust the width of the table according to the terminal's width."""
    terminal_width = get_terminal_width()
    num_columns = len(table_instance.table_data[0])
    column_width = terminal_width // num_columns
    table_instance.column_max_width = {index: column_width - 3 for index in range(num_columns)}

def pass_the_captcha():
    """Handles the CAPTCHA challenge for the given onion website and returns URL_TOKEN."""
    url_index = "http://4wbwa6vcpvcr3vvf4qkhppgy56urmjcj2vagu2iqgp3z656xcmfdbiqd.onion/"
    req = requests.get(url_index, verify=False, proxies={'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'})
    soup = BeautifulSoup(req.text, "html.parser")
    get_captcha = soup.find('pre').text
    get_id = soup.find('input', {'name': 'id'}).get('value')
    print(get_captcha)

    captcha = input("Enter the captcha: ")
    url_captcha = "{}captcha".format(url_index)

    datas = {
        "captcha": captcha,
        "id": get_id
    }

    req_captcha = requests.post(url_captcha, verify=False, data=datas, proxies={'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'})
    return req_captcha.url.split("=")[-1]


def main(URL_TOKEN=None, max_results=None):
    """Main function to scrape and display data from the onion website"""
    URL_TOKEN = pass_the_captcha()  # Get URL_TOKEN

    # Filter out parameters that are empty
    filtered_params = {key: value for key, value in params.items() if value}
    search_url = "http://4wbwa6vcpvcr3vvf4qkhppgy56urmjcj2vagu2iqgp3z656xcmfdbiqd.onion/search?" + "&".join(f"{key}={value}" for key, value in filtered_params.items())
    search_url += "&s={}&r=*any*&g=*any*".format(URL_TOKEN)
    
    # Use the Tor proxy for the request
    with requests.Session() as session:
        session.verify = False
        session.proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
        response = session.get(search_url, allow_redirects=True)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Handle CAPTCHA if presented
    if "fill" in response.text:
        # Use tqdm for the progress bar
        for _ in tqdm(range(10), desc="Processing before CAPTCHA", unit="step"):
            time.sleep(0.1)
        pass_the_captcha()
    else:
        table = soup.find('table')
        if table:
            headers = [th.text.strip() for th in table.find_all('th')]
            data = []

            # Use tqdm for the progress bar
            for row in tqdm(table.find_all('tr')[1:], desc="Processing rows", unit="row"):
                row_data = [td.text.strip() for td in row.find_all('td')]
                data.append(row_data)

                # Check if max_results is specified and reached
                if max_results is not None and len(data) >= max_results:
                    break

            # Adjust and print the data table
            table_instance = SingleTable([headers] + data)
            adjust_table_width(table_instance)
            table_instance.inner_heading_row_border = False
            table_instance.inner_row_border = True
            table_instance.justify_columns = {index: 'center' for index in range(len(headers))}
            print(table_instance.table)
            print("\nDirect Link to Facebook profile:\n")
            for row in data:
                fb_url = f"https://www.facebook.com/profile.php?id={row[0]}"
                print(fb_url)
            save_results(data)
        else:
            print("\nNo results found.")

clear_screen()
banner_lines = display_banner()
for line in banner_lines:
    print(Fore.RED + line + Style.RESET_ALL)
    time.sleep(0.1)

if __name__ == '__main__':
    # Parse arguments from the command line
    parser = argparse.ArgumentParser(description='Tool to search for information in a Facebook dump')
    parser.add_argument('-i', '--id', help='ID')
    parser.add_argument('-f', '--firstname', help='First name')
    parser.add_argument('-l', '--lastname', help='Last name')
    parser.add_argument('-t', '--phone', help='Phone number')
    parser.add_argument('-w', '--work', help='Work')
    parser.add_argument('-o', '--location', help='Location')
    parser.add_argument('-m', '--max-results', type=int, help='Maximum number of results to display')
    args = parser.parse_args()

    # Check if any arguments were provided
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    # Create a dictionary with all the provided search parameters
    params = {
        'i': args.id if args.id else '',
        'f': args.firstname if args.firstname else '',
        'l': args.lastname if args.lastname else '',
        't': args.phone if args.phone else '',
        'w': args.work if args.work else '',
        'o': args.location if args.location else ''
    }
    main(URL_TOKEN=None, max_results=args.max_results)
