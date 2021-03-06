# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from keeper import Wad, Address
from keeper.api.approval import directly
from keeper.api.token import DSToken
from keeper.sai_maker_otc_cancel import SaiMakerOtcCancel
from tests.conftest import SaiDeployment
from tests.helper import args


class TestSaiMakerOtcCancel:
    def test_should_cancel_offers_owned_by_us(self, sai: SaiDeployment):
        # given
        keeper = SaiMakerOtcCancel(args=args(f"--eth-from {sai.web3.eth.defaultAccount}"),
                                   web3=sai.web3, config=sai.get_config())

        # and
        DSToken(web3=sai.web3, address=sai.gem.address).mint(Wad.from_number(1000)).transact()
        DSToken(web3=sai.web3, address=sai.sai.address).mint(Wad.from_number(1000)).transact()

        # and
        sai.otc.approve([sai.gem, sai.sai], directly())
        sai.otc.make(sai.gem.address, Wad.from_number(10), sai.sai.address, Wad.from_number(5)).transact()
        sai.otc.make(sai.sai.address, Wad.from_number(5), sai.gem.address, Wad.from_number(12)).transact()
        assert len(sai.otc.active_offers()) == 2

        # when
        keeper.startup()
        keeper.shutdown()

        # then
        assert len(sai.otc.active_offers()) == 0

    def test_should_ignore_offers_owned_by_others(self, sai: SaiDeployment):
        # given
        keeper = SaiMakerOtcCancel(args=args(f"--eth-from {sai.web3.eth.defaultAccount}"),
                                   web3=sai.web3, config=sai.get_config())

        # and
        DSToken(web3=sai.web3, address=sai.gem.address).mint(Wad.from_number(1000)).transact()
        DSToken(web3=sai.web3, address=sai.sai.address).mint(Wad.from_number(1000)).transact()

        # and
        sai.gem.transfer(Address(sai.web3.eth.accounts[1]), Wad.from_number(500)).transact()
        sai.sai.transfer(Address(sai.web3.eth.accounts[1]), Wad.from_number(500)).transact()

        # and
        sai.otc.approve([sai.gem, sai.sai], directly())
        sai.otc.make(sai.gem.address, Wad.from_number(10), sai.sai.address, Wad.from_number(5)).transact()

        # and
        sai.web3.eth.defaultAccount = sai.web3.eth.accounts[1]
        sai.otc.approve([sai.gem, sai.sai], directly())
        sai.otc.make(sai.sai.address, Wad.from_number(5), sai.gem.address, Wad.from_number(12)).transact()
        sai.web3.eth.defaultAccount = sai.web3.eth.accounts[0]

        # and
        assert len(sai.otc.active_offers()) == 2

        # when
        keeper.startup()
        keeper.shutdown()

        # then
        assert len(sai.otc.active_offers()) == 1
        assert sai.otc.active_offers()[0].owner == Address(sai.web3.eth.accounts[1])

    def test_should_use_gas_price_specified(self, sai: SaiDeployment):
        # given
        some_gas_price = 15000000000
        keeper = SaiMakerOtcCancel(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --gas-price {some_gas_price}"),
                                   web3=sai.web3, config=sai.get_config())

        # and
        DSToken(web3=sai.web3, address=sai.gem.address).mint(Wad.from_number(1000)).transact()
        DSToken(web3=sai.web3, address=sai.sai.address).mint(Wad.from_number(1000)).transact()

        # and
        sai.otc.approve([sai.gem, sai.sai], directly())
        sai.otc.make(sai.sai.address, Wad.from_number(5), sai.gem.address, Wad.from_number(12)).transact()
        assert len(sai.otc.active_offers()) == 1

        # when
        keeper.startup()
        keeper.shutdown()

        # then
        assert len(sai.otc.active_offers()) == 0
        assert sai.web3.eth.getBlock('latest', True)['transactions'][0]['gasPrice'] == some_gas_price
