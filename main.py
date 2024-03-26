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

TOKEN_FILE = 'captcha_token.txt'

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
    padding = 3
    column_min_width = 15

    available_width = terminal_width - (num_columns * padding)
    column_width = max(available_width // num_columns, column_min_width)

    table_instance.column_max_width = {index: column_width for index in range(num_columns)}


def adjust_table_width_fixed_max(table_instance, max_width=50):
    """Adjust the width of the table to a fixed maximum width."""
    num_columns = len(table_instance.table_data[0])
    column_width = max_width // num_columns
    table_instance.column_max_width = {index: column_width for index in range(num_columns)}


def truncate_content(content, max_width):
    """Tronquer le contenu des cellules pour qu'il ne dépasse pas la largeur maximale."""
    return (content[:max_width - 3] + '...') if len(content) > max_width else content

def adjust_table_width_dynamic(table_instance, max_column_width=20):
    """Adjust the table's column widths based on content, with a maximum width and content truncation."""
    terminal_width = get_terminal_width()
    content_widths = [max(len(str(cell)) for cell in column) for column in zip(*table_instance.table_data)]
    content_widths = [min(max_column_width, width) for width in content_widths]

    total_content_width = sum(content_widths) + (len(content_widths) - 1) * 3
    if total_content_width > terminal_width:
        scale_factor = terminal_width / total_content_width
        content_widths = [max(5, int(width * scale_factor)) for width in content_widths]

    for i, width in enumerate(content_widths):
        table_instance.column_max_width[i] = width
        for row in table_instance.table_data:
            row[i] = truncate_content(str(row[i]), width)



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
    save_captcha_token(req_captcha.url.split("=")[-1])
    return req_captcha.url.split("=")[-1]

def save_captcha_token(token):
    """Sauvegarder le token captcha dans un fichier."""
    with open(TOKEN_FILE, 'w') as file:
        file.write(token)


def read_captcha_token():
    """Lire le token captcha depuis un fichier. Retourne None si le fichier n'existe pas."""
    try:
        with open(TOKEN_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def clean_input(input_string):
    return input_string.strip()

def main(URL_TOKEN=None, max_results=None):
    """Main function to scrape and display data from the onion website"""
    URL_TOKEN = read_captcha_token()
    if not URL_TOKEN:
        URL_TOKEN = pass_the_captcha()

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
            adjust_table_width_dynamic(table_instance)
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
        'i': clean_input(args.id) if args.id else '',
        'f': clean_input(args.firstname) if args.firstname else '',
        'l': clean_input(args.lastname) if args.lastname else '',
        't': args.phone if args.phone else '',
        'w': args.work if args.work else '',
        'o': args.location if args.location else ''
    }
    main(URL_TOKEN=None, max_results=args.max_results)
