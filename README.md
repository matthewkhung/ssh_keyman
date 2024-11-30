# SSH Key Manager

This tool helps manage SSH private keys stored in a LUKS file vault and interacts with SSH-agent.

## Prerequisites

This program requires cryptsetup and must be installed before use. Running the program will also require root access.

## Creating a LUKS File Vault

SSH keys are stored in a LUKS file vault. The following command will create a LUKS vault <code>ssh_key_vault.luks</code>.

<code>ssh-keyman create-vault ssh_key_vault.luks</code>

## Adding Keys

Keys can be generated using the <code>ssh-keygen</code> application. The following command will generate a private key
using the Ed25519 signing algorithm with the name <code>id_ed25519_host_user</code> and a corresponding public key
<code>id_ed25519_host_user.pub</code>.

<code>ssh-keygen -t ed25519 -C "user@host_name" -f "id_ed25519_host_user"</code>

The public key can be distributed to remote servers and used to validate this host. The private key must be kept secure.
This can be accomplished by adding it to the LUKS vault created above. Use the following command to add the private key
to the vault named <code>ssh_key_vault.luks</code>.

<code>ssh-keyman add-keys ssh_key_vault.luks -k id_id25519_host_user</code>

Multiples can be added in the same command.

<code>ssh-keyman add-keys ssh_key_vault.luks -k id_id25519_host_user_1 -k id_id25519_host_user_2</code>

## Load Keys

Now that the vault contains some SSH keys, they can be loaded into ssh-agent with the following command. The application
takes care of opening and closing the vault.

<code>ssh-keyman load-keys ssh_key_vault.luks</code>

## Unload Keys

This command is a simple wrapper to remove all keys from the ssh-agent. Note that this will unload ALL keys and not
just the ones added from the vault.

<code>ssh-keyman unload-keys</code>

## List Keys

Use the following command to review the list of private keys stored in the vault.

<code>ssh-keyman list-keys ssh_key_vault.luks</code>

## Remove Keys

The following command will walk you through the process of selecting and removing keys.

<code>ssh-keyman remove-keys ssh_key_vault.luks</code>
