from unittest import mock

import pytest

from ssh_keyman.luks_utils import close_luks_vault, create_luks_vault, open_luks_vault


class TestLuksUtils:
    ssh_keyman_dev = "ssh_keyman"
    ssh_keyman_mnt = "/mnt/ssh_keyman"

    def test_create_luks_vault(self, mocker):
        """Normal flow of create_luks_vault."""
        # mock
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("os.path.exists", return_value=False)
        mocker.patch("getpass.getpass", side_effect=["password", "password"])
        mock_encrypt_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.encrypt_luks_container"
        )
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_mkfs_luks_dev = mocker.patch("ssh_keyman.luks_utils.mkfs_luks_dev")
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        mock_remove = mocker.patch("os.remove")
        # run
        create_luks_vault("test_vault.luks", 32)
        # assert
        mock_open.assert_called_once_with("test_vault.luks", "xb")
        mock_encrypt_luks_container.assert_called_once_with(
            "password", "test_vault.luks"
        )
        mock_open_luks_container.assert_called_once_with(
            "password", "test_vault.luks", self.ssh_keyman_dev
        )
        mock_mkfs_luks_dev.assert_called_once_with("ssh_keyman")
        mock_close_luks_container.assert_called_once_with("ssh_keyman")
        mock_remove.assert_not_called()

    def test_create_luks_vault_file_exists(self, mocker):
        """Exception flow create_luks_vault when open raises a FileExistError."""
        # mock
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("getpass.getpass", side_effect=["password", "password"])
        mock_encrypt_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.encrypt_luks_container"
        )
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_mkfs_luks_dev = mocker.patch("ssh_keyman.luks_utils.mkfs_luks_dev")
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        mock_remove = mocker.patch("os.remove")
        with pytest.raises(FileExistsError):
            # run
            create_luks_vault("test_vault.luks", 32)
        # assert
        mock_open.assert_not_called()
        mock_encrypt_luks_container.assert_not_called()
        mock_open_luks_container.assert_not_called()
        mock_mkfs_luks_dev.assert_not_called()
        mock_close_luks_container.assert_not_called()
        mock_remove.assert_not_called()

    def test_open_luks_vault_no_mnt(self, mocker):
        """Normal flow of open_luks_vault with no mount point created"""
        # mock
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_subprocess = mocker.patch("subprocess.run")
        mocker.patch("os.path.isdir", return_value=False)
        # mocker.patch("os.listdir", return_value=[])
        mocker.patch("os.path.ismount", return_value=False)
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        open_luks_vault("test_vault.luks", "password")
        # assert
        mock_open_luks_container.assert_called_once_with(
            "password", "test_vault.luks", self.ssh_keyman_dev
        )
        calls = [
            mock.call(["sudo", "mkdir", self.ssh_keyman_mnt], check=True),
            mock.call(
                [
                    "sudo",
                    "mount",
                    f"/dev/mapper/{self.ssh_keyman_dev}",
                    self.ssh_keyman_mnt,
                ],
                check=True,
            ),
        ]
        mock_subprocess.assert_has_calls(calls, any_order=False)
        mock_close_luks_container.assert_not_called()

    def test_open_luks_vault_empty_mnt(self, mocker):
        """Normal flow of open_luks_vault with an empty mount directory (not mounted)"""
        # mock
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_subprocess = mocker.patch("subprocess.run")
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.listdir", return_value=[])
        mocker.patch("os.path.ismount", return_value=False)
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        open_luks_vault("test_vault.luks", "password")
        # assert
        mock_open_luks_container.assert_called_once_with(
            "password", "test_vault.luks", self.ssh_keyman_dev
        )
        calls = [
            mock.call(
                [
                    "sudo",
                    "mount",
                    f"/dev/mapper/{self.ssh_keyman_dev}",
                    self.ssh_keyman_mnt,
                ],
                check=True,
            ),
        ]
        mock_subprocess.assert_has_calls(calls, any_order=False)
        mock_close_luks_container.assert_not_called()

    def test_open_luks_vault_non_empty_mnt(self, mocker):
        """
        Exception flow of open_luks_vault with a non-empty mount directory
        (not mounted)
        """
        # mock
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_subprocess = mocker.patch("subprocess.run")
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.listdir", return_value=["test.txt"])
        mocker.patch("os.path.ismount", return_value=False)
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        with pytest.raises(PermissionError):
            open_luks_vault("test_vault.luks", "password")
        # assert
        mock_open_luks_container.assert_called_once_with(
            "password", "test_vault.luks", self.ssh_keyman_dev
        )
        mock_subprocess.assert_not_called()
        mock_close_luks_container.assert_called_once_with(self.ssh_keyman_dev)

    def test_open_luks_vault_used_mnt(self, mocker):
        """Exception flow of open_luks_vault with an occupied mount point"""
        # mock
        mock_open_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.open_luks_container"
        )
        mock_subprocess = mocker.patch("subprocess.run")
        mocker.patch("os.path.isdir", return_value=False)
        mocker.patch("os.listdir", return_value=[])
        mocker.patch("os.path.ismount", return_value=True)
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        with pytest.raises(PermissionError):
            open_luks_vault("test_vault.luks", "password")
        # assert
        mock_open_luks_container.assert_called_once_with(
            "password", "test_vault.luks", self.ssh_keyman_dev
        )
        calls = [
            mock.call(["sudo", "mkdir", self.ssh_keyman_mnt], check=True),
        ]
        mock_subprocess.assert_has_calls(calls, any_order=False)
        mock_close_luks_container.assert_called_once_with(self.ssh_keyman_dev)

    def test_close_luks_vault(self, mocker):
        """Normal flow of close_luks_vault."""
        # mock
        mocker.patch("os.path.ismount", return_value=True)
        mock_subprocess = mocker.patch("subprocess.run")
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        close_luks_vault()
        # assert
        calls = [
            mock.call(["sudo", "umount", self.ssh_keyman_mnt], check=True),
            mock.call(["sudo", "rmdir", self.ssh_keyman_mnt], check=True),
        ]
        mock_subprocess.assert_has_calls(calls, any_order=False)
        mock_close_luks_container.assert_called_once_with(self.ssh_keyman_dev)

    def test_close_luks_vault_not_mounted(self, mocker):
        """Exception flow of close_luks_vault where dev is not mounted."""
        # mock
        mocker.patch("os.path.ismount", return_value=False)
        mock_subprocess = mocker.patch("subprocess.run")
        mock_close_luks_container = mocker.patch(
            "ssh_keyman.luks_utils.close_luks_container"
        )
        # run
        close_luks_vault()
        # assert
        calls = [
            mock.call(["sudo", "rmdir", self.ssh_keyman_mnt], check=True),
        ]
        mock_subprocess.assert_has_calls(calls, any_order=False)
        mock_close_luks_container.assert_called_once_with(self.ssh_keyman_dev)
