
Built by https://www.blackbox.ai

---

```markdown
# Plesk Account Management Bot

## Project Overview
This project is a Telegram bot that allows users to manage their Plesk hosting accounts. Users can create accounts, view their transaction history, and manage wallet balances using cryptocurrency payments via the NOWPayments API. The bot is designed to enhance the user experience by providing an interactive interface integrated with backend APIs for account management and cryptocurrency transactions.

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/plesk-account-management-bot.git
   cd plesk-account-management-bot
   ```

2. **Install the required Python packages**. Make sure you have Python 3.x installed and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**. Create a `.env` file or export the following variables in your shell:
   ```bash
   export PLESK_HOST="your_plesk_host"
   export PLESK_USERNAME="your_plesk_username"
   export PLESK_PASSWORD="your_plesk_password"
   export NOWPAYMENTS_API_KEY="your_nowpayments_api_key"
   export NOWPAYMENTS_IPN_SECRET="your_nowpayments_ipn_secret"
   ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```
   
5. **Run the Flask application** (for admin dashboard):
   ```bash
   python app.py
   ```

## Usage
1. Start the bot on Telegram by searching for it by the token you obtained from the BotFather.
2. Use the command `/start` to initiate interaction.
3. Follow the on-screen prompts to manage subscriptions, view your wallet, and make deposits.

## Features
- **User Management**: Create, manage, and delete users.
- **Wallet Balance Management**: Users can deposit and view their wallet balance.
- **Plesk API Integration**: Create and manage hosting accounts through Plesk's API.
- **Transaction History**: Users can view their transaction history.
- **Crypto Payments**: Facilitate payments via cryptocurrencies using the NOWPayments API.
- **Admin Dashboard**: Monitor user statistics and transactions via a web interface.

## Dependencies
The project depends on the following Python packages, which are listed in `requirements.txt`:
- Flask
- Requests
- python-telegram-bot
- json
- os
- fcntl

Install them using:
```bash
pip install -r requirements.txt
```

## Project Structure
```
plesk-account-management-bot/
│
├── app.py                 # Flask web application for admin management
├── bot.py                 # Telegram bot main logic
├── data_manager.py        # Functions to manage user data and transactions
├── nowpayments.py         # Integration with NOWPayments API for cryptocurrency payments
└── plesk_api.py           # Integration with Plesk API for managing hosting accounts
```

### Data Structure
- **users.db** (Stored as JSON):
  - `users`: List of user objects with properties `id`, `username`, `wallet_balance`, `subscription`, and `history`.
  - `offers`: List of available hosting offers.

## Contributing
Feel free to submit issues and pull requests. Ensure your code follows best practices, and write tests for new features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
This README provides a complete guide for setting up and using the project, alongside an outline of features and the structure of the codebase.