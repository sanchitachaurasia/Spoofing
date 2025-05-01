import random, logging
global_id_counter = 1

class Order:
    def __init__(self, order_id, order_type, price, amount, agent_id=None, order_time=None):
        self.agent_id = agent_id
        self.order_id = order_id
        self.order_type = order_type  # 'buy' or 'sell'
        self.order_time = order_time  # Timestamp of the order
        self.price = price
        self.qty = amount
        
        self.filled_qty = 0  # This is only for the order book to keep track of the filled quantity

    def __repr__(self):
        return f"Order({self.order_id}:: {self.order_type} @ {self.price} for {self.qty} by {self.agent_id})"


class User:
    def __init__(self, user_id, initial_balance, initial_shares, logger=None):
        self.user_id = user_id
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.shares = initial_shares
        self.initial_shares = initial_shares
        self.logger = logger or logging.getLogger(__name__)
        self.pending_orders = {}
        self.orders_executed = {}
        self.commitable_shares = initial_shares
        self.commitable_balance = initial_balance

    def generate_order(self, current_price):
        """Generate a random order within user's financial constraints"""
        if self.commitable_balance <= 0 and self.commitable_shares <= 0:
            return None
        global global_id_counter
        order_id = global_id_counter
        illegal_order = True
        # Decide order type based on available resources
        while illegal_order:
            if random.random() < 0.5:
                order_type = 'buy'
                max_quantity = int((self.commitable_balance / current_price) * 0.5)
                quantity = random.randint(1, max_quantity)
                price = random.randint(int((current_price or 100) * 0.6), int((current_price or 100) * 1.4))
                if quantity * price < self.commitable_balance:
                    illegal_order = False
                self.logger.debug(f"The user can commit {self.commitable_balance} balance")
                self.commitable_balance -= quantity * price
                self.logger.debug(f"The user can commit {self.commitable_balance} balance after the order id {order_id} for {quantity} shares @ {price}")
            else:
                order_type = 'sell'
                self.logger.debug(f"The user can commit {self.commitable_shares} shares")
                max_quantity = int(self.commitable_shares * 0.5)
                quantity = random.randint(1, max_quantity)
                price = random.randint(int((current_price or 100) * 0.6), int((current_price or 100) * 1.4))
                if quantity < self.commitable_shares:
                    illegal_order = False
                self.commitable_shares -= quantity
                self.logger.debug(f"The user can commit {self.commitable_shares} shares after the order id {order_id} for {quantity} shares @ {price}")

        assert self.commitable_balance >= 0, f"User {self.user_id} has negative balance after order generation!"
        assert self.commitable_shares >= 0, f"User {self.user_id} has negative shares after order generation!"

        if max_quantity <= 0:
            return None
        
        global_id_counter += 1
        self.pending_orders[order_id] = Order(
            order_id=order_id,
            order_type=order_type,
            price=price,
            amount=quantity,
            agent_id=self.user_id
        )
        self.logger.info(f"User {self.user_id} generated order: {self.pending_orders[order_id]}")
        return self.pending_orders[order_id]

    def notify(self, order, filled_quantity, price, is_canceled=False):
        """Handle order execution/cancellation notifications"""
        # print(f"User {self.user_id} notified: Order {order.order_id} filled with {filled_quantity} shares at {price:.2f}")
        if order.order_id in self.pending_orders:
            self.orders_executed[order.order_id] = self.pending_orders[order.order_id]

        if is_canceled:
            self.logger.info(f"User {self.user_id}: Order {order.order_id} canceled")
            return

        if order.order_type == 'buy':
            self.balance -= filled_quantity * price
            self.commitable_balance = self.commitable_balance - filled_quantity * (price - self.pending_orders[order.order_id].price)
            self.shares += filled_quantity
            self.commitable_shares += filled_quantity
            action = "bought"
        else:
            self.shares -= filled_quantity
            self.balance += filled_quantity * price
            self.commitable_balance = self.commitable_balance + filled_quantity * (price)
            action = "sold"

        self.logger.info(
            f"User {self.user_id} {action} {filled_quantity} shares @ {price:.2f}. "
            f"New balance: {self.balance:.2f}, shares: {self.shares}"
        )
