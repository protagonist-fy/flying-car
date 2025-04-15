import os
import random
import requests
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from tronpy.keys import PrivateKey
from colorama import Fore, Style, init

init(autoreset=True)

# Counters
valid_count = 0
invalid_count = 0
hit_count = 0

# ---------- GENERATE MNEMONICS ----------
def load_word_list(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines()]

def generate_mnemonics(word_list, count=10000):  # Adjust count as needed
    return [" ".join(random.sample(word_list, 12)) for _ in range(count)]

# ---------- PROCESS MNEMONICS ----------
def derive_tron_address(mnemonic_phrase: str):
    try:
        seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
        bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        private_key = PrivateKey(bytes.fromhex(bip44_acc.PrivateKey().Raw().ToHex()))
        return private_key.public_key.to_base58check_address(), private_key.hex()
    except Exception:
        return None, None

def get_usdt_balance(address: str):
    TRONGRID_API_URL = f"https://apilist.tronscan.org/api/account?address={address}"
    response = requests.get(TRONGRID_API_URL)
    if response.status_code == 200:
        data = response.json()
        for token in data.get("trc20token_balances", []):
            if token.get("tokenName") == "Tether USD":
                return float(token.get("balance", 0)) / (10 ** 6)
    return 0

def process_mnemonic(mnemonic_phrase):
    global valid_count, invalid_count, hit_count
    tron_address, private_key = derive_tron_address(mnemonic_phrase)
    if not tron_address:
        print(f"{Fore.RED}[Invalid] Mnemonic: {mnemonic_phrase}{Style.RESET_ALL}\n")
        with open("results/bad.txt", "a") as bad_file:
            bad_file.write(mnemonic_phrase + "\n\n")
        invalid_count += 1
        return

    valid_count += 1
    usdt_balance = get_usdt_balance(tron_address)
    print(f"{Fore.CYAN}12 Words Mnemonic Phrase:{Fore.YELLOW} {mnemonic_phrase}\n")
    print(f"{Fore.LIGHTGREEN_EX}USDT(TRC) Address:{Fore.YELLOW} {tron_address}\n")
    print(f"{Fore.LIGHTYELLOW_EX}Private Key:{Fore.YELLOW} {private_key}\n")
    print(f"{Fore.BLUE}Balance:{Fore.YELLOW} {usdt_balance} USDT\n\n")

    result_line = f"{mnemonic_phrase} | {tron_address} | {private_key} | {usdt_balance} USDT\n\n"
    with open("results/good.txt", "a") as good_file:
        good_file.write(result_line)

    if usdt_balance > 0:
        hit_count += 1
        with open("results/hits.txt", "a") as hits_file:
            hits_file.write(result_line)

# ---------- MAIN ----------
def main():
    global valid_count, invalid_count, hit_count
    os.makedirs("results", exist_ok=True)
    open("results/good.txt", "a").close()
    open("results/bad.txt", "a").close()
    open("results/hits.txt", "a").close()

    word_list = load_word_list("english.txt")
    mnemonics = generate_mnemonics(word_list)

    for mnemonic in mnemonics:
        process_mnemonic(mnemonic.strip())

    os.system('cls' if os.name == 'nt' else 'clear')
    total = valid_count + invalid_count
    print(f"{Fore.GREEN}Checking Completed!\n")
    print(f"- Hits: {Fore.CYAN}{hit_count}")
    print(f"- Valids: {Fore.LIGHTGREEN_EX}{valid_count}")
    print(f"- Invalids: {Fore.LIGHTRED_EX}{invalid_count}")
    print(f"- Total: {Fore.YELLOW}{total}\n")
    input("Press Any Key To Exit...")

if __name__ == "__main__":
    main()
