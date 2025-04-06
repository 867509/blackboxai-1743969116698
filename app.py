from flask import Flask, render_template, request, jsonify, redirect, url_for
from data_manager import load_data, save_data
from plesk_api import PleskAPI
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Plesk API
plesk = PleskAPI(
    host=os.getenv('PLESK_HOST'),
    username=os.getenv('PLESK_USERNAME'),
    password=os.getenv('PLESK_PASSWORD')
)

@app.route('/')
def dashboard():
    """Admin dashboard with statistics"""
    data = load_data()
    
    # Calculate statistics
    total_users = len(data.get('users', []))
    active_subscriptions = sum(1 for u in data.get('users', []) if u.get('subscription'))
    total_revenue = sum(tx['amount'] for u in data.get('users', []) for tx in u.get('history', []) if tx['type'] == 'purchase')
    
    # Recent transactions
    recent_transactions = []
    for user in data.get('users', []):
        for tx in user.get('history', [])[-5:]:  # Get last 5 transactions per user
            recent_transactions.append({
                'user_id': user['id'],
                'username': user.get('username'),
                'type': tx['type'],
                'amount': tx['amount'],
                'currency': tx.get('currency'),
                'timestamp': tx['timestamp']
            })
    
    # Sort by timestamp (newest first)
    recent_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('dashboard.html',
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        total_revenue=total_revenue,
        recent_transactions=recent_transactions[:10]  # Show top 10
    )

@app.route('/users')
def users():
    """User management page"""
    data = load_data()
    return render_template('users.html', users=data.get('users', []))

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_detail(user_id):
    """View and edit user details"""
    data = load_data()
    user = next((u for u in data.get('users', []) if u['id'] == user_id), None)
    
    if not user:
        return "User not found", 404
    
    if request.method == 'POST':
        # Update user data
        user['wallet_balance'] = float(request.form.get('wallet_balance', 0))
        
        if user.get('subscription'):
            user['subscription']['expiry'] = request.form.get('expiry_date')
            
            # Update Plesk if needed
            if 'plesk_plan_id' in request.form:
                plesk.update_subscription(
                    user['subscription']['plesk_client_id'],
                    request.form['plesk_plan_id']
                )
        
        save_data(data)
        return redirect(url_for('user_detail', user_id=user_id))
    
    return render_template('user_detail.html', user=user)

@app.route('/offers')
def offers():
    """Offer management page"""
    data = load_data()
    return render_template('offers.html', offers=data.get('offers', []))

@app.route('/offer/add', methods=['GET', 'POST'])
def add_offer():
    """Add new offer"""
    if request.method == 'POST':
        data = load_data()
        new_offer = {
            'id': len(data.get('offers', [])) + 1,
            'name': request.form.get('name'),
            'price': float(request.form.get('price')),
            'duration_days': int(request.form.get('duration_days')),
            'plesk_plan_id': request.form.get('plesk_plan_id')
        }
        data['offers'].append(new_offer)
        save_data(data)
        return redirect(url_for('offers'))
    
    return render_template('add_offer.html')

@app.route('/offer/<int:offer_id>/edit', methods=['GET', 'POST'])
def edit_offer(offer_id):
    """Edit existing offer"""
    data = load_data()
    offer = next((o for o in data.get('offers', []) if o['id'] == offer_id), None)
    
    if not offer:
        return "Offer not found", 404
    
    if request.method == 'POST':
        offer['name'] = request.form.get('name')
        offer['price'] = float(request.form.get('price'))
        offer['duration_days'] = int(request.form.get('duration_days'))
        offer['plesk_plan_id'] = request.form.get('plesk_plan_id')
        save_data(data)
        return redirect(url_for('offers'))
    
    return render_template('edit_offer.html', offer=offer)

@app.route('/offer/<int:offer_id>/delete', methods=['POST'])
def delete_offer(offer_id):
    """Delete offer"""
    data = load_data()
    data['offers'] = [o for o in data.get('offers', []) if o['id'] != offer_id]
    save_data(data)
    return redirect(url_for('offers'))

@app.route('/plesk')
def plesk_actions():
    """Plesk API actions page"""
    return render_template('plesk.html')

@app.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    """Handle NOWPayments webhook notifications"""
    from nowpayments import NOWPayments
    np = NOWPayments(
        api_key=os.getenv('NOWPAYMENTS_API_KEY'),
        ipn_secret=os.getenv('NOWPAYMENTS_IPN_SECRET')
    )
    
    if np.verify_webhook(request.json, request.headers.get('x-nowpayments-sig')):
        if np.process_webhook(request.json):
            return jsonify({'status': 'success'}), 200
    
    return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)