import pandas as pd
import streamlit as st

# Set page title
st.title("Crypto Transactions Dashboard")
st.write("Upload your transactions data and crypto prices to generate detailed user wallet breakdowns.")

# Step 1: Upload Transactions CSV
st.header("Step 1: Upload Transactions CSV")
transactions_file = st.file_uploader("Upload Transactions CSV", type=["csv"])

if transactions_file:
    transactions = pd.read_csv(transactions_file)
    st.write("### Transactions Data Preview:")
    st.dataframe(transactions.head())

    # Check required columns
    required_columns = [
        'transaction_type', 'user_id', 'wallet_public_address',
        'transaction_date', 'denomination', 'units'
    ]
    if not all(col in transactions.columns for col in required_columns):
        st.error(f"Missing required columns. Ensure your CSV contains: {', '.join(required_columns)}")
        st.stop()

    # Step 2: Input Crypto Prices
    st.header("Step 2: Input Crypto Prices")
    unique_denominations = transactions['denomination'].unique()

    # Option to upload crypto prices CSV
    crypto_prices = {}
    use_csv = st.checkbox("Upload a Crypto Prices CSV instead of manual input")
    if use_csv:
        prices_file = st.file_uploader("Upload Crypto Prices CSV", type=["csv"])
        if prices_file:
            price_df = pd.read_csv(prices_file)
            if 'denomination' in price_df.columns and 'price' in price_df.columns:
                crypto_prices = dict(zip(price_df['denomination'], price_df['price']))
                st.write("### Crypto Prices Loaded:")
                st.dataframe(price_df)
            else:
                st.error("Crypto Prices CSV must have 'denomination' and 'price' columns.")
                st.stop()
    else:
        st.write("Enter USD values for the following cryptocurrencies:")
        for denom in unique_denominations:
            price = st.number_input(f"Enter USD value for {denom}:", min_value=0.0, value=0.0, step=0.01)
            crypto_prices[denom] = price

    if not crypto_prices:
        st.error("Please provide crypto prices to continue.")
        st.stop()

    # Save crypto prices for future reference
    crypto_prices_df = pd.DataFrame(list(crypto_prices.items()), columns=['Denomination', 'Price'])
    crypto_prices_path = "crypto_prices.csv"
    crypto_prices_df.to_csv(crypto_prices_path, index=False)
    st.write(f"Crypto prices saved to {crypto_prices_path}")

    # Step 3: Process Transactions
    st.header("Step 3: Processing Transactions")

    # Map prices and calculate USD values
    transactions['price'] = transactions['denomination'].map(crypto_prices)
    transactions['usd_value'] = transactions['units'] * transactions['price']

    # Aggregate user data with breakdowns
    user_totals = transactions.groupby('user_id').agg(
        total_usd=('usd_value', 'sum'),
        wallet_address=('wallet_public_address', 'first')
    ).reset_index()

    # Pivot for breakdowns
    breakdown_pivot = transactions.pivot_table(
        index='user_id',
        columns='denomination',
        values=['units', 'usd_value'],
        aggfunc='sum',
        fill_value=0
    )
    breakdown_pivot.columns = [f"{col[1]} {col[0]}" for col in breakdown_pivot.columns]
    breakdown_pivot.reset_index(inplace=True)

    # Merge user totals with breakdowns
    breakdown_df = pd.merge(user_totals, breakdown_pivot, on='user_id', how='left')

    # Step 4: Generate Outputs
    st.header("Step 4: Outputs")

    output_options = st.multiselect(
        "Select outputs to download:",
        ["Summary", "Users Between $250 and $2500", "Users Above $2500", "All Users"],
        default=["Summary", "Users Between $250 and $2500"]
    )

    # 4.1: Users between $100 and $2500
    if "Users Between $250 and $2500" in output_options:
        users_250_to_2500 = breakdown_df[(breakdown_df['total_usd'] >= 250) & (breakdown_df['total_usd'] <= 2500)]
        st.subheader("Users Between $100 and $2500")
        st.dataframe(users_250_to_2500)
        st.download_button(
            "Download Users Between $100 and $2500",
            users_250_to_2500.to_csv(index=False),
            "users_250_to_2500_with_breakdown.csv"
        )

    # 4.2: Users above $2500
    if "Users Above $2500" in output_options:
        users_above_2500 = breakdown_df[breakdown_df['total_usd'] > 2500]
        st.subheader("Users Above $2500")
        st.dataframe(users_above_2500)
        st.download_button(
            "Download Users Above $2500",
            users_above_2500.to_csv(index=False),
            "users_above_2500_with_breakdown.csv"
        )

    # 4.3: Summary
    if "Summary" in output_options:
        total_users = breakdown_df.shape[0]
        users_above_100 = breakdown_df[breakdown_df['total_usd'] > 250].shape[0]
        total_usd = breakdown_df['total_usd'].sum()

        # Asset breakdown
        total_assets = transactions.groupby('denomination').agg(
            total_units=('units', 'sum'),
            total_usd=('usd_value', 'sum')
        ).reset_index()

        summary_data = {
            "Metric": ["Total Users", "Users Above $100", "Total USD Value Held"],
            "Value": [total_users, users_above_100, total_usd]
        }
        summary_df = pd.DataFrame(summary_data)

        st.subheader("Summary")
        st.dataframe(summary_df)
        st.download_button(
            "Download Summary",
            summary_df.to_csv(index=False),
            "summary.csv"
        )

        st.subheader("Total Asset Breakdown")
        st.dataframe(total_assets)
        st.download_button(
            "Download Asset Breakdown",
            total_assets.to_csv(index=False),
            "asset_breakdown.csv"
        )

    # 4.4: All Users
    if "All Users" in output_options:
        st.subheader("All Users")
        st.dataframe(breakdown_df)
        st.download_button(
            "Download All Users",
            breakdown_df.to_csv(index=False),
            "all_users_with_breakdown.csv"
        )
