import getpass
import logging
import os
import subprocess

ssh_keyman_dev = "ssh_keyman"
ssh_keyman_mnt = "/mnt/ssh_keyman"


def encrypt_luks_container(passphrase, vault_path):
    """
    Turn file into an encrypted LUKS block device.
    """
    cmd = ["sudo", "cryptsetup", "luksFormat", vault_path, "--batch-mode"]
    subprocess.run(cmd, input=f"{passphrase}\n".encode(), check=True)
    logging.debug(f"Created LUKS container at {vault_path}.")


def open_luks_container(passphrase, vault_path, dev):
    """
    Open a LUKS block device.
    """
    cmd = ["sudo", "cryptsetup", "open", "--type", "luks", vault_path, dev]
    subprocess.run(cmd, input=f"{passphrase}\n".encode(), check=True)
    logging.debug(f"Opened LUKS container at /dev/mapper/{dev}.")


def close_luks_container(dev):
    """
    Close a LUKS block device.
    """
    subprocess.run(["sudo", "cryptsetup", "close", dev], check=False)
    logging.debug(f"Closed LUKS device {dev}.")


def mkfs_luks_dev(dev):
    """
    Format a LUKS block device with an EXT4 filesystem.
    """
    cmd = ["sudo", "mkfs.ext4", f"/dev/mapper/{dev}"]
    subprocess.run(cmd, check=True)
    logging.debug(f"Created ext4 filesystem on /dev/mapper/{dev}.")


def create_luks_vault(vault_path, size_MB):
    """
    Create a LUKS file vault.
    """
    vault_created = False
    vault_is_open = False
    try:
        # check the file does not exist
        if os.path.exists(vault_path):
            raise FileExistsError(f"{vault_path} already exists.")

        # prompt for passphrase
        passphrase = getpass.getpass("Enter a passphrase to secure the key vault: ")
        confirm_passphrase = getpass.getpass("Enter the passphrase again: ")
        if passphrase != confirm_passphrase:
            raise ValueError("Passphrases do not match.")

        # create empty file
        with open(vault_path, "xb") as f:
            f.truncate(size_MB * 1024 * 1024)
        vault_created = True
        logging.debug(f"Empty file created at {vault_path} ({size_MB} MB).")

        # encrypt as LUKS container
        encrypt_luks_container(passphrase, vault_path)

        # open LUKS container
        open_luks_container(passphrase, vault_path, ssh_keyman_dev)
        vault_is_open = True

        # create filesystem on LUKS device
        mkfs_luks_dev(ssh_keyman_dev)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}.")
        if vault_created:
            # delete vault
            os.remove(vault_path)
            logging.debug(f"Deleted vault at {vault_path}.")
        raise

    except Exception as e:
        print(f"Error: {e}")
        if vault_created:
            # delete vault
            os.remove(vault_path)
            logging.debug(f"Deleted vault at {vault_path}.")
        raise

    finally:
        if vault_is_open:
            # close the vault
            close_luks_container(ssh_keyman_dev)


def open_luks_vault(vault_path, passphrase):
    """
    Open a LUKS file vault and mount it
    """
    vault_is_open = False
    try:
        # open LUKS container
        open_luks_container(passphrase, vault_path, ssh_keyman_dev)
        vault_is_open = True

        # check for mount point
        if os.path.isdir(ssh_keyman_mnt):
            if len(os.listdir(ssh_keyman_mnt)):
                raise PermissionError(f"Mount point is not empty {ssh_keyman_mnt}")
        else:
            cmd = ["sudo", "mkdir", ssh_keyman_mnt]
            subprocess.run(cmd, check=True)
            logging.debug(f"Created mount point at {ssh_keyman_mnt}")

        # check if mount point is in use
        if os.path.ismount(ssh_keyman_mnt):
            raise PermissionError(f"Mount point already in use {ssh_keyman_mnt}")

        # mount to mount point
        cmd = ["sudo", "mount", f"/dev/mapper/{ssh_keyman_dev}", ssh_keyman_mnt]
        subprocess.run(cmd, check=True)
        logging.debug(f"Mounted /dev/mapper/{ssh_keyman_dev} at {ssh_keyman_mnt}")

        return ssh_keyman_mnt

    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}.")
        if vault_is_open:
            # close the vault
            close_luks_container(ssh_keyman_dev)
        raise

    except Exception as e:
        print(f"Error: {e}")
        if vault_is_open:
            # close the vault
            close_luks_container(ssh_keyman_dev)
        raise


def close_luks_vault():
    """
    Close a LUKS file vault
    """
    try:
        # unmount
        if os.path.ismount(ssh_keyman_mnt):
            cmd = ["sudo", "umount", ssh_keyman_mnt]
            subprocess.run(cmd, check=True)
            logging.debug(f"Unmounted {ssh_keyman_mnt}")
        else:
            logging.warning("Unmount unsuccessful, mount point not in use")

        # remove mount point
        cmd = ["sudo", "rmdir", ssh_keyman_mnt]
        subprocess.run(cmd, check=True)
        logging.debug(f"Removed mount point at {ssh_keyman_mnt}")

        # close vault
        close_luks_container(ssh_keyman_dev)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}.")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise
