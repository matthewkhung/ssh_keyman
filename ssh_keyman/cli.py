import getpass
import logging
import os

import click

from ssh_keyman.keys_utils import (
    copy_ssh_key,
    delete_ssh_key,
    get_ssh_key_list,
    load_ssh_key,
    unload_ssh_keys,
)
from ssh_keyman.luks_utils import close_luks_vault, create_luks_vault, open_luks_vault


@click.group()
@click.option("-v", "--verbose", count=True, help="Increase verbosity level.")
def ssh_keyman(verbose):
    """
    SSH Key Manager

    This tool helps manage SSH private keys stored in a LUKS file vault and interacts
    with SSH-agent.
    """
    # Set up logging based on verbosity level
    if verbose == 0:
        logging.basicConfig(level=logging.WARNING)
    elif verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    pass


@ssh_keyman.command(name="create-vault")
@click.argument("vault_path", type=click.Path(exists=False))
def create_vault(vault_path):
    """
    Create a LUKS file vault to store SSH keys.
    """
    try:
        create_luks_vault(vault_path, 32)
        logging.info(f"Key vault created at {vault_path}")
    except Exception as e:
        logging.error(f"Error: {e}")


@ssh_keyman.command(name="add-keys")
@click.argument("vault_path", type=click.Path(exists=True))
@click.option(
    "-k",
    "--key-path",
    "keys",
    type=click.Path(exists=True),
    multiple=True,
    help="Path to SSH keys.",
)
def add_keys(vault_path, keys):
    """
    Add an SSH private key to the LUKS vault.
    """
    try:
        # prompt for passphrase
        passphrase = getpass.getpass("Enter vault passphrase: ")
        # open vault
        mnt = open_luks_vault(vault_path, passphrase)
        existing_keys = get_ssh_key_list(mnt)
        cnt = 0
        for key in keys:
            # check for existing key
            if key in existing_keys:
                if not click.confirm(f"Override existing key ({key})?"):
                    # skip override
                    logging.info("Key not added to vault")
                    continue
            # copy/override key
            copy_ssh_key(key, mnt)
            logging.info("Added key to vault")
            cnt += 1
        print(f"{cnt} keys added to vault")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        close_luks_vault()


@ssh_keyman.command(name="list-keys")
@click.argument("vault_path", type=click.Path(exists=True))
def list_keys(vault_path):
    """
    List keys stored in the vault
    """
    try:
        # prompt for passphrase
        passphrase = getpass.getpass("Enter vault passphrase: ")
        # open vault
        mnt = open_luks_vault(vault_path, passphrase)
        keys = get_ssh_key_list(mnt)
        if not keys:
            print("No keys in vault.")
            return
        # display keys in vault
        print("Keys in vault:")
        for idx, key in enumerate(keys, start=1):
            print(f"{idx:2d}) {key}")
    except Exception as e:
        logging.error(f"Error: {e}")
        raise
    finally:
        close_luks_vault()


@ssh_keyman.command(name="remove-keys")
@click.argument("vault_path", type=click.Path(exists=True))
def remove_keys(vault_path):
    """
    Remove an SSH private key from the LUKS vault.
    """
    try:
        # prompt for passphrase
        passphrase = getpass.getpass("Enter vault passphrase: ")
        # read keys in vault
        mnt = open_luks_vault(vault_path, passphrase)
        keys = get_ssh_key_list(mnt)
        if not keys:
            print("No keys in vault.")
            return
        # display keys in vault
        print("Select keys to delete:")
        for idx, key in enumerate(keys):
            print(f"{idx:2d}) {key}")
        close_luks_vault()
        mnt = None

        # prompt for choice
        choice_type = click.Choice(["none", "all"] + [str(x) for x in range(len(keys))])
        choice = click.prompt(
            f"Which key would you like to delete? (none, all, 0 - {len(keys)})",
            value_proc=str.lower,
            type=choice_type,
            default="none",
            show_choices=False,
        )
        if choice == "none":
            print("No keys deleted.")
            return
        elif choice == "all":
            if not click.confirm("Are you sure you want to delete all keys?"):
                print("No keys deleted.")
                return
            # delete all keys
            mnt = open_luks_vault(vault_path, passphrase)
            for key in keys:
                delete_ssh_key(os.path.join(mnt, key))
        else:
            choice = int(choice)
            if not click.confirm(f"Are you sure you want to delete {keys[choice]}?"):
                print("No keys deleted.")
                return
            # delete selected key
            mnt = open_luks_vault(vault_path, passphrase)
            delete_ssh_key(os.path.join(mnt, keys[choice]))

    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        if mnt:
            close_luks_vault()


@ssh_keyman.command(name="load-keys")
@click.argument("vault_path", type=click.Path(exists=True))
def load_keys(vault_path):
    """
    Load SSH keys into the SSH-agent from the LUKS vault.
    """
    # prompt for passphrase
    passphrase = getpass.getpass("Enter vault passphrase: ")
    mnt = open_luks_vault(vault_path, passphrase)
    keys = get_ssh_key_list(mnt)
    for key in keys:
        load_ssh_key(key)
    close_luks_vault()
    print("Keys loaded")


@ssh_keyman.command(name="unload-keys")
def unload_keys():
    """
    Unload SSH keys from the SSH-agent.
    """
    unload_ssh_keys()
    print("Keys unloaded")


if __name__ == "__main__":
    ssh_keyman()
