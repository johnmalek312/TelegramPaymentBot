# Payment and Chat Support Bot

This project is a template for setting up a payment and chat support bot. The bot integrates with PayPal, credit card payments, and cryptocurrency transactions. It connects with both Discord and Telegram functionality and uses a Flask web server. Please note that there are known bugs, and the database table will need to be rebuilt and connected to a database for full functionality.

## Features

- **Integration**: Linked with Discord and Telegram.
- **Chat Support**: Includes chat support feature.
- **Payment Gateways**: Supports PayPal, credit card, and cryptocurrency payments.
- **QR Code Generation**: Includes functionality for QR code creation for easier payments or sharing.

## Requirements

This project requires the following dependencies, which are listed in the `requirements.txt` file:

```
requests~=2.32.3
python-dateutil~=2.9.0.post0
python-telegram-bot
Flask
mysql-connector-python
discord.py
python-dotenv
qrcode
clipboard
```

You can install the dependencies using:

```bash
pip install -r requirements.txt
```

## Getting Started

1. Clone the repository to your local machine.
   
   ```bash
   git clone https://github.com/your-username/TelegramPaymentBot.git
   ```

2. Navigate to the project directory:

   ```bash
   cd TelegramPaymentBot
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables by creating a `.env` file. Refer to the provided `.env` file template and configure your own values.

5. **Database Setup**: The database connection and tables need to be configured. Review the `sql.py` file to understand the necessary queries, and set up your MySQL database accordingly.

6. **Running the Project**: Run the Flask application or the bot services (Discord, Telegram) as needed.

   ```bash
   python main.py
   ```

## Known Issues

- **Database Setup**: The current codebase requires a fresh database setup. You may need to remake the database tables and ensure they are properly connected.
- **Bug Fixes**: This template contains some bugs that need to be addressed for full functionality.

## How to Contribute

1. Fork the repository.
2. Create a new branch..
3. Make your changes.
4. Commit and push your changes.
5. Open a pull request.
