import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from data_manager import get_user, update_wallet, add_transaction
from plesk_api import PleskAPI
from nowpayments import NOWPayments
import random
import string

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PleskBot:
    def __init__(self, token, plesk_config, nowpayments_config):
        self.application = Application.builder().token(token).build()
        self.plesk = PleskAPI(**plesk_config)
        self.nowpayments = NOWPayments(**nowpayments_config)
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message with main menu"""
        user = update.effective_user
        user_data = get_user(user.id)
        
        if not user_data:
            # Create new user if doesn't exist
            user_data = {
                "id": user.id,
                "username": user.username,
                "wallet_balance": 0,
                "subscription": None,
                "history": []
            }
            from data_manager import load_data, save_data
            data = load_data()
            data["users"].append(user_data)
            save_data(data)
        
        keyboard = [
            [InlineKeyboardButton("💰 My Wallet", callback_data="wallet")],
            [InlineKeyboardButton("🛒 Buy Account", callback_data="buy")],
            [InlineKeyboardButton("📜 History", callback_data="history")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n"
            "Please choose an option:",
            reply_markup=reply_markup
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "wallet":
            await self.show_wallet(query)
        elif query.data == "buy":
            await self.show_offers(query)
        elif query.data == "history":
            await self.show_history(query)
        elif query.data.startswith("offer_"):
            await self.process_offer(query)
        elif query.data == "deposit":
            await self.request_deposit(query)
        elif query.data.startswith("currency_"):
            await self.create_payment(query)
    
    async def show_wallet(self, query):
        """Display user's wallet balance and options"""
        user = get_user(query.from_user.id)
        balance = user.get("wallet_balance", 0)
        
        keyboard = [
            [InlineKeyboardButton("💳 Deposit", callback_data="deposit")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💰 Your Wallet Balance: ${balance:.2f}\n\n"
            "Choose an option:",
            reply_markup=reply_markup
        )
    
    async def show_offers(self, query):
        """Display available Plesk account offers"""
        from data_manager import load_data
        data = load_data()
        offers = data.get("offers", [])
        
        keyboard = []
        for offer in offers:
            keyboard.append([
                InlineKeyboardButton(
                    f"{offer['name']} - ${offer['price']}",
                    callback_data=f"offer_{offer['id']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛒 Available Plesk Accounts:\n\n"
            "Please select an offer:",
            reply_markup=reply_markup
        )
    
    async def process_offer(self, query):
        """Process user's selection of an offer"""
        offer_id = int(query.data.split("_")[1])
        from data_manager import load_data
        data = load_data()
        offer = next((o for o in data["offers"] if o["id"] == offer_id), None)
        user = get_user(query.from_user.id)
        
        if not offer:
            await query.edit_message_text("❌ Offer not found!")
            return
        
        if user.get("wallet_balance", 0) < offer["price"]:
            await query.edit_message_text(
                "❌ Insufficient funds!\n"
                f"You need ${offer['price']} but only have ${user.get('wallet_balance', 0):.2f}\n\n"
                "Would you like to deposit funds?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Deposit Now", callback_data="deposit")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back")]
                ])
            )
            return
        
        # Process purchase
        if not user.get("subscription"):
            # Create new Plesk client
            client = self.plesk.create_client()
            subscription = self.plesk.create_subscription(
                client["plesk_client_id"],
                offer["plesk_plan_id"]
            )
            
            # Update user data
            user["subscription"] = {
                "plan": offer["name"],
                "expiry": "2024-12-31",  # Should calculate based on duration
                "plesk_client_id": client["plesk_client_id"],
                "credentials": {
                    "username": client["username"],
                    "password": client["password"],
                    "domain": subscription["domain"]
                }
            }
            update_wallet(query.from_user.id, -offer["price"])
            add_transaction(
                user_id=query.from_user.id,
                transaction_type="purchase",
                amount=-offer["price"]
            )
            
            # Send credentials to user
            await query.edit_message_text(
                "🎉 Purchase Successful!\n\n"
                f"🔑 Username: {client['username']}\n"
                f"🔒 Password: {client['password']}\n"
                f"🌐 Domain: {subscription['domain']}\n\n"
                "Thank you for your purchase!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
        else:
            # Existing user - just update subscription
            self.plesk.update_subscription(
                user["subscription"]["plesk_client_id"],
                offer["plesk_plan_id"]
            )
            update_wallet(query.from_user.id, -offer["price"])
            add_transaction(
                user_id=query.from_user.id,
                transaction_type="purchase",
                amount=-offer["price"]
            )
            
            await query.edit_message_text(
                "🎉 Subscription Updated!\n\n"
                f"Your account has been upgraded to {offer['name']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
    
    async def request_deposit(self, query):
        """Show deposit options with supported cryptocurrencies"""
        currencies = self.nowpayments.get_currencies()
        
        keyboard = []
        for currency in currencies:
            keyboard.append([
                InlineKeyboardButton(
                    currency.upper(),
                    callback_data=f"currency_{currency}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        reply_markup =InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💳 Deposit Funds\n\n"
            "Select cryptocurrency:",
            reply_markup=reply_markup
        )
    
    async def create_payment(self, query):
        """Create a crypto payment invoice"""
        currency = query.data.split("_")[1]
        order_id = f"deposit_{query.from_user.id}_{random.randint(1000, 9999)}"
        
        await query.edit_message_text(
            "💳 Deposit Funds\n\n"
            "Please enter the amount in USD you wish to deposit:"
        )
        
        # Store context for the next message
        context.user_data["awaiting_amount"] = True
        context.user_data["currency"] = currency
        context.user_data["order_id"] = order_id
    
    async def handle_deposit_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the amount entered by user and create payment"""
        if not context.user_data.get("awaiting_amount"):
            return
        
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid positive number!")
            return
        
        currency = context.user_data["currency"]
        order_id = context.user_data["order_id"]
        user_id = update.effective_user.id
        
        try:
            payment = self.nowpayments.create_payment(
                amount=amount,
                currency=currency,
                order_id=order_id,
                user_id=user_id
            )
            
            await update.message.reply_text(
                f"💳 Payment Request Created\n\n"
                f"Amount: ${amount:.2f}\n"
                f"Currency: {currency.upper()}\n\n"
                f"Please send the equivalent amount to:\n"
                f"<code>{payment['pay_address']}</code>\n\n"
                f"Payment ID: {payment['payment_id']}\n"
                f"Expires in: {payment['expiration_estimate_date']}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Payment creation failed: {str(e)}")
            await update.message.reply_text(
                "❌ Failed to create payment request. Please try again later."
            )
        
        # Clear context
        context.user_data.clear()
    
    async def show_history(self, query):
        """Show user's transaction history"""
        user = get_user(query.from_user.id)
        history = user.get("history", [])
        
        if not history:
            await query.edit_message_text(
                "📜 No transactions found!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back")]
                ])
            )
            return
        
        history_text = "📜 Transaction History:\n\n"
        for tx in history[-10:]:  # Show last 10 transactions
            amount = f"+${tx['amount']}" if tx['amount'] > 0 else f"-${abs(tx['amount'])}"
            currency = tx.get('currency', '').upper()
            history_text += (
                f"🕒 {tx['timestamp']}\n"
                f"💵 {amount} {currency}\n"
                f"📝 {tx['type'].capitalize()}\n\n"
            )
        
        await query.edit_message_text(
            history_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
    
    def run(self):
        """Start the bot"""
        # Add handler for deposit amount
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_deposit_amount)
        )
        
        self.application.run_polling()