import tonsdk
from tonsdk.utils import Address, InvalidAddressError
from tonsdk.contract.wallet import WalletVersionEnum, Wallets
from ..Contracts.Contract import Contract, Cell
from tonsdk.utils import bytes_to_b64str
import tonsdk.contract.token.ft
from tonsdk.contract.token.nft import NFTItem

class WalletError(BaseException):
    pass


class Wallet(Contract):
    def __init__(self, provider, address: str = None, mnemonics: list = None, version='v4r2'):
        self.provider = provider
        if address:
            self.address = address
            self.full_data = False
        if mnemonics:
            mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(mnemonics, WalletVersionEnum(version), 0)
            self.mnemonics = mnemonics
            self.version = version
            self.address = self.provider._process_address(wallet.address.to_string())
            self.full_data = True
        if not address and not mnemonics:
            mnemonics, _pub_k, _priv_k, wallet = Wallets.create(WalletVersionEnum(version), 0)
            self.mnemonics = mnemonics
            self.version = version
            self.address = self.provider._process_address(wallet.address.to_string())
            self.full_data = True
        super().__init__(self.address, provider)

    def has_access(self):
        return self.full_data

    async def get_seqno(self):
        return await self.provider.get_wallet_seqno(self.address)

    async def transfer_ton(self, destination_address: str, amount: float, message: Cell | bytes | str = '', send_mode: int = 3):
        if not self.has_access():
            raise WalletError('Cannot send tons from wallet without wallet mnemonics\nCreate wallet like Wallet(mnemonics=["your", "mnemonic", "here"...], version="your_wallet_version")')
        mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(self.mnemonics, WalletVersionEnum(self.version), 0)
        seqno = await self.get_seqno()
        query = wallet.create_transfer_message(to_addr=destination_address,
                                               amount=tonsdk.utils.to_nano(amount, 'ton'),
                                               seqno=seqno, payload=message, send_mode=send_mode)
        boc = bytes_to_b64str(query["message"].to_boc(False))
        response = await self.provider.send_boc(boc)
        return response

    async def transfer_jetton_by_jetton_wallet(self, destination_address: str, jetton_wallet: str, jettons_amount: float, fee: float = 0.06, decimals: int = 9):
        """
        Better to use .transfer_jetton().
        """
        if not self.has_access():
            raise WalletError('Cannot send jettons from wallet without wallet mnemonics\nCreate wallet like Wallet(mnemonics=["your", "mnemonic", "here"...], version="your_wallet_version")')
        mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(self.mnemonics, WalletVersionEnum(self.version), 0)
        seqno = await self.get_seqno()
        body = tonsdk.contract.token.ft.JettonWallet().create_transfer_body(
            Address(destination_address),
            jettons_amount * 10**decimals
        )
        query = wallet.create_transfer_message(
            jetton_wallet,
            tonsdk.utils.to_nano(fee, "ton"),
            seqno,
            payload=body
        )

        jettons_boc = bytes_to_b64str(query["message"].to_boc(False))
        response = await self.provider.send_boc(jettons_boc)
        return response

    async def transfer_jetton(self, destination_address: str, jetton_master_address: str, jettons_amount: float, fee: float = 0.06):
        if not self.has_access():
            raise WalletError('Cannot send jettons from wallet without wallet mnemonics\nCreate wallet like Wallet(mnemonics=["your", "mnemonic", "here"...], version="your_wallet_version")')

        mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(self.mnemonics, WalletVersionEnum(self.version), 0)
        seqno = await self.get_seqno()
        jetton = await self.provider.get_jetton_data(jetton_master_address)
        body = tonsdk.contract.token.ft.JettonWallet().create_transfer_body(
            Address(destination_address),
            jettons_amount * 10**jetton.decimals
        )
        jetton_wallet = await jetton.get_jetton_wallet(self.address)
        query = wallet.create_transfer_message(
            jetton_wallet.address,
            tonsdk.utils.to_nano(fee, "ton"),
            seqno,
            payload=body
        )

        jettons_boc = bytes_to_b64str(query["message"].to_boc(False))
        response = await self.provider.send_boc(jettons_boc)
        return response

    async def deploy(self):
        if not self.has_access():
            raise WalletError('Cannot deploy wallet without wallet mnemonics\nCreate wallet like Wallet(mnemonics=["your", "mnemonic", "here"...], version="your_wallet_version")')
        mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(self.mnemonics, WalletVersionEnum(self.version), 0)
        query = wallet.create_init_external_message()
        boc = bytes_to_b64str(query["message"].to_boc(False))
        response = await self.provider.send_boc(boc)
        return response

    async def transfer_nft(self, destination_address: str, nft_address: str, fee: float = 0.02):
        if not self.has_access():
            raise WalletError('Cannot send nft from wallet without wallet mnemonics\nCreate wallet like Wallet(mnemonics=["your", "mnemonic", "here"...], version="your_wallet_version")')
        mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(self.mnemonics, WalletVersionEnum(self.version), 0)
        seqno = await self.get_seqno()
        body = NFTItem().create_transfer_body(
            Address(destination_address)
        )
        query = wallet.create_transfer_message(
            nft_address,
            tonsdk.utils.to_nano(fee, "ton"),
            seqno,
            payload=body
        )
        nft_boc = bytes_to_b64str(query["message"].to_boc(False))
        response = await self.provider.send_boc(nft_boc)
        return response
