from brownie import network
from brownie.network.main import show_active
from scripts.helpful_scripts import get_account
from web3 import Web3
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from brownie import network, config, interface

amount = AMOUNT = Web3.toWei(0.1, "ether")


def main():
    print("Aave borrow")
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # ABI and Address
    lending_pool = get_lending_pool()
    # Deposit ERC20 ETH into lending_pool
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Let's borrow some DAI")
    # DAI in terms of ETH
    dai_eth_price_feed = config["networks"][network.show_active()]["dai_eth_price_feed"]
    dai_eth_price = get_asset_price(dai_eth_price_feed)
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable eth -> borrowable dai * 95%
    print(f"We are going to borrow { amount_dai_to_borrow}")
    # Now we will borrow!
    dai_address = config["networks"][network.show_active()]["dai_token"]
    inWei_amount_dai_to_borrow = Web3.toWei(amount_dai_to_borrow, "ether")
    borrow_tx = lending_pool.borrow(
        dai_address,
        inWei_amount_dai_to_borrow,
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some dai")
    get_borrowable_data(lending_pool, account)
    # repay_all(amount, lending_pool, account)
    print("All worked fine.")


def repay_all(amount, lending_pool, account):
    print("Repaying all..")
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )

    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )

    repay_tx.wait(1)
    print("Repayed!")


def get_asset_price(price_feed_address):
    # ABI and an address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    # dai_eth_price_feed now is a contract we can interact with.
    latestPrice = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latestPrice, "ether")
    print(f"DAI latest price: {converted_latest_price}")
    return float(converted_latest_price)


def get_lending_pool():
    # ABI and address

    print("Get lending pool address..")

    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )

    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # ABI
    # Address - Check!
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")
    return tx


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))
