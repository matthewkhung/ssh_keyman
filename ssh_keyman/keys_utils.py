import logging
import os
import subprocess


def copy_ssh_key(src, dest):
    """
    Copy SSH keys to destination while keeping ownership.
    """
    try:
        # copy keys and keep permissions
        cmd = ["sudo", "cp", "-p", src, dest]
        subprocess.run(cmd, check=True)
        logging.debug(f"SSH key {src} copied to {dest}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def get_ssh_key_list(mnt):
    """
    List keys stored at mount point.
    """
    # read keys in vault
    keys = []
    for file in os.listdir(mnt):
        # check for file
        if os.path.isfile(file):
            keys.append(file)
    return keys


def delete_ssh_key(path):
    """
    Delete key at path
    """
    try:
        # copy keys and keep permissions
        cmd = ["sudo", "rm", path]
        subprocess.run(cmd, check=True)
        logging.debug(f"Deleted SSH key {path}")
        print(f"Deleted key {path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def load_ssh_key(key_path):
    """
    Loads key into SSH-agent.
    """
    try:
        # add keys to agent
        cmd = ["sudo", "ssh-add", key_path]
        subprocess.run(cmd, check=True)
        logging.debug(f"Key {key_path} added to ssh-agent")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def unload_ssh_keys():
    """
    Unloads all keys in SSH-agent.
    """
    try:
        # add keys to agent
        cmd = ["sudo", "ssh-add", "-D"]
        subprocess.run(cmd, check=True)
        logging.debug("All keys removed from ssh-agent")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: Command failed with code {e.returncode}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
