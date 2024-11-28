import pytest
from click.testing import CliRunner

import ssh_keyman.cli


@pytest.fixture
def runner():
    return CliRunner()


class TestLuksUtils:

    def test_version(self):
        assert ssh_keyman.__version__ == "0.1.0"

    def test_create_vault(self, runner, mocker):
        """Normal flow of create_vault."""
        # mock
        mock_create_vault = mocker.patch("ssh_keyman.cli.create_luks_vault")
        # run
        result = runner.invoke(
            ssh_keyman.cli.ssh_keyman, ["create-vault", "test_vault.luks"]
        )
        # assert
        assert result.exit_code == 0
        mock_create_vault.assert_called_once_with("test_vault.luks", 32)

    def test_list_keys(self, runner, mocker):
        """Normal flow of list_vault."""
        # mock
        mocker.patch("getpass.getpass", side_effect=["password"])
        mock_open_vault = mocker.patch(
            "ssh_keyman.cli.open_luks_vault", return_value="/mnt/test"
        )
        mock_list_keys = mocker.patch(
            "ssh_keyman.cli.get_ssh_key_list", return_value=["key1", "key2"]
        )
        mock_close_vault = mocker.patch("ssh_keyman.cli.close_luks_vault")
        # run
        with runner.isolated_filesystem():
            with open("test_vault.luks", "w") as f:
                f.write("")
            result = runner.invoke(
                ssh_keyman.cli.ssh_keyman, ["list-keys", "test_vault.luks"]
            )
        # assert
        assert result.exit_code == 0
        assert "key1" in result.output
        assert "key2" in result.output
        mock_open_vault.assert_called_once()
        mock_list_keys.assert_called_once()
        mock_close_vault.assert_called_once()
