import re

import httpx
import pydantic
import pytest

import eospyo


def test_should_always_pass():
    pass


def test_when_instantiate_net_returns_net_object():
    net = eospyo.Net(host="http://127.0.0.1:8888")
    assert isinstance(net, eospyo.Net)


def test_when_instantiate_net_with_incorrect_host_format_then_raises_error():
    with pytest.raises(pydantic.ValidationError):
        eospyo.Net(host="rpc://127.0.0.1:8888")


def test_when_net_get_info_then_returns_dict(net):
    info = net.get_info()
    assert isinstance(info, dict)


def test_given_http_timeout_when_net_get_info_then_raise_connection_error(
    httpx_mock, net
):
    with pytest.raises(eospyo.exc.ConnectionError):
        net.get_info()


def test_given_http_write_error_when_net_get_info_then_raise_connection_error(
    httpx_mock, net
):
    def raise_write_error(*args, **kwargs):
        raise httpx.WriteError("")

    httpx_mock.add_callback(raise_write_error)
    with pytest.raises(eospyo.exc.ConnectionError):
        net.get_info()


def test_given_http_return_400_when_net_get_info_then_raise_connection_error(
    httpx_mock, net
):
    httpx_mock.add_response(status_code=400)
    with pytest.raises(eospyo.exc.ConnectionError):
        net.get_info()


def test_when_net_get_info_then_return_has_chain_id(net):
    info = net.get_info()
    assert "chain_id" in info


def test_when_net_get_info_then_chain_id_has_correct_format(net):
    info = net.get_info()
    patt = r"[a-f0-9]{64}"
    assert re.fullmatch(patt, info["chain_id"])


def test_when_instantiate_waxtestnet_then_host_has_tld():
    net = eospyo.WaxTestnet()
    patt = r"^https://[\w\.]{3,}"
    assert re.match(patt, net.host)


def test_when_instantiate_localnet_then_host_is_localhost():
    net = eospyo.Local()
    assert net.host.startswith("http://127.0.0.1")


accounts = ["eosio", "user1", "user2"]


@pytest.mark.parametrize("account_name", accounts)
def test_when_get_account_X_then_return_has_account_name(net, account_name):
    account_info = net.get_account(account_name=account_name)
    assert "account_name" in account_info


@pytest.mark.parametrize("account_name", accounts)
def test_when_get_account_X_then_return_account_name_match(net, account_name):
    account_info = net.get_account(account_name=account_name)
    assert account_info["account_name"] == account_name


def test_when_get_non_existing_account(net):
    resp = net.get_account(account_name="qweasdzxc")
    assert resp["error"]["details"][0]["message"].startswith("unknown key")


def test_user1_has_no_abi(net):
    abi = net.get_abi(account_name="user1")
    assert abi is None


def test_user2_has_an_abi(net):
    abi = net.get_abi(account_name="user2")
    assert abi is not None


def test_when_get_abi_then_returns_has_account_name(net):
    abi = net.get_abi(account_name="user2")
    assert "account_name" in abi


def test_when_get_abi_then_returned_abi_account_name_matches(net):
    abi = net.get_abi(account_name="user2")
    abi["account_name"] == "user2"


def test_get_block_previous_field_is_000(net):
    block = net.get_block(block_num_or_id=1)
    assert block["previous"] == "0" * 64


def test_get_block_info_previous_field_is_000(net):
    block = net.get_block_info(block_num=1)
    assert block["previous"] == "0" * 64


def test_abi_json_to_bin_return_bytes(net):
    json = {"from": "abcdef", "message": "a sample message"}
    bindata = net.abi_json_to_bin(
        account_name="user2",
        action="sendmsg",
        json=json,
    )
    assert isinstance(bindata, bytes)


def test_abi_bin_to_json_return_dict(net):
    json = {"from": "abcdef", "message": "a sample message"}
    bindata = net.abi_json_to_bin(
        account_name="user2",
        action="sendmsg",
        json=json,
    )
    d = net.abi_bin_to_json(
        account_name="user2",
        action="sendmsg",
        bytes=bindata,
    )
    assert isinstance(d, dict)


def test_abi_json_to_bin_and_bin_to_json_return_same_as_sent(net):
    json = {"from": "abcdef", "message": "a sample message"}
    bindata = net.abi_json_to_bin(
        account_name="user2",
        action="sendmsg",
        json=json,
    )
    d = net.abi_bin_to_json(
        account_name="user2",
        action="sendmsg",
        bytes=bindata,
    )
    assert d == json