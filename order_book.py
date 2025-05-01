import time
from copy import deepcopy
import logging
from utils import Order, User



class OrderBook:
    def __init__(self, logger:logging.Logger=None):
        self.buy_orders:list[Order] = []
        self.sell_orders:list[Order] = [] 
        self.last_trade_price = None
        self.order_id_counter = 1
        self.fee_percentage = 0.1  # Fee percentage (e.g., 0.1% fee)
        self.logger = logger
        self.logger.debug("OrderBook initialized.")
        self.registered_users:dict[int, User] = {}  # Dictionary to hold registered 
        # self.logger:logging.Logger = logger if logger else logging.getLogger(__name__)

    def register_user(self, user:User):
        """Register a user to the order book."""
        if user.user_id in self.registered_users:
            self.logger.warning(f"User {user.user_id} is already registered.")
            return False
        self.registered_users[user.user_id] = user
        self.logger.info(f"User {user.user_id} registered successfully.")
        return True

    def process_matched_orders(self, matched_orders, active_order, qty_to_match=None):
        """Processes matched orders and updates the order book accordingly."""
        self.logger.debug(f"Processing matched orders: {matched_orders} with active order: {active_order}")
        if not matched_orders:
            self.logger.debug("No matched orders found.")
            if active_order.order_type == 'buy':
                self.buy_orders.insert(0, active_order)
                # Sort by highest price, lowest time
                self.buy_orders.sort(key=lambda x: (-x.price, x.order_time))
                self.logger.debug(f"Active order added to buy orders: {active_order}")
            else:
                self.sell_orders.insert(0, active_order)
                self.sell_orders.sort(key=lambda x: (x.price, x.order_time))
                self.logger.debug(f"Active order added to sell orders: {active_order}")
            return matched_orders  # No matched orders to process
        
        # Set last trade price to the filled_qty weighted average of the matched orders
        self.last_trade_price = sum(order.price * order.filled_qty for order in matched_orders) / sum(order.filled_qty for order in matched_orders)
        self.logger.debug(f"Last trade price set to: {self.last_trade_price}")

        # This means some orders were matched
        self.logger.debug(f"Matched orders: {matched_orders}")
        if active_order.order_type == 'buy':
            self.sell_orders = self.sell_orders[len(matched_orders):]
            # Notify all but the last matched order
            for order in matched_orders[:-1]:
                self.registered_users[order.agent_id].notify(
                    order=order,
                    filled_quantity=order.filled_qty,
                    price=order.price
                )
                # print logger in red font
                self.logger.info(f"ROUTE X !!! User {order.agent_id}: Order {order.order_id} executed for {order.filled_qty} shares at {order.price}")

            if matched_orders[-1].qty != 0:
                # Prepend the remaining order to the sell orders
                self.sell_orders.insert(0, matched_orders[-1])
                self.sell_orders.sort(key=lambda x: (x.price, x.order_time))  # Sort sell orders by price (lowest first)
                self.logger.debug(f"Partial match, remaining order: {matched_orders[-1]}, adding to sell orders.")

            # Notify the last matched order
            self.registered_users[matched_orders[-1].agent_id].notify(
                order=matched_orders[-1],
                filled_quantity=matched_orders[-1].filled_qty,
                price=matched_orders[-1].price
            ) if matched_orders[-1].filled_qty != 0 else None
            self.logger.info(f"ROUTE A !!! User {matched_orders[-1].agent_id}: Order {matched_orders[-1].order_id} partially/fully executed for {matched_orders[-1].filled_qty} shares at {matched_orders[-1].price}\033[0m")

            # Notify the active order about matching
            if active_order.agent_id in self.registered_users:
                self.registered_users[active_order.agent_id].notify(
                    order=active_order,
                    filled_quantity=active_order.qty - qty_to_match,
                    price=self.last_trade_price
                ) if active_order.qty - qty_to_match != 0 else None
                self.logger.info(f"ROUTE D !!! User {active_order.agent_id}: Order {active_order.order_id} partially/fully executed for {active_order.qty - qty_to_match} shares at {self.last_trade_price}\033[0m")
            else:
                self.logger.error(f"Active order {active_order.order_id} not found in registered users.")

            
            if qty_to_match != 0:
                # Prepend the remaining order to the buy orders
                active_order.qty = qty_to_match
                self.buy_orders.insert(0, active_order)
                self.buy_orders.sort(key=lambda x: (-x.price, x.order_time))
                self.logger.debug(f"Partial match, remaining order: {active_order}, adding to buy orders.")

        else:
            self.buy_orders = self.buy_orders[len(matched_orders):]
            # Notify all but the last matched order
            for order in matched_orders[:-1]:
                self.registered_users[order.agent_id].notify(
                    order=order,
                    filled_quantity=order.filled_qty,
                    price=order.price
                )
                # print logger in red font
                self.logger.info(f"ROUTE B !!! User {order.agent_id}: Order {order.order_id} executed for {order.filled_qty} shares at {order.price}\033[0m")
            if matched_orders[-1].qty != 0:
                # Prepend the remaining order to the buy orders
                self.buy_orders.insert(0, matched_orders[-1])
                self.buy_orders.sort(key=lambda x: (-x.price, x.order_time))
                self.logger.debug(f"Partial match, remaining order: {matched_orders[-1]}, adding to buy orders.")

            # Notify the last matched order
            self.registered_users[matched_orders[-1].agent_id].notify(
                order=matched_orders[-1],
                filled_quantity=matched_orders[-1].filled_qty,
                price=matched_orders[-1].price
            ) if matched_orders[-1].filled_qty != 0 else None

            self.logger.info(f"ROUTE C !!! User {matched_orders[-1].agent_id}: Order {matched_orders[-1].order_id} partially/fully executed for {matched_orders[-1].filled_qty} shares at {matched_orders[-1].price}\033[0m")

            # Notify the active order about matching
            if active_order.agent_id in self.registered_users:
                self.registered_users[active_order.agent_id].notify(
                    order=active_order,
                    filled_quantity=active_order.qty - qty_to_match,
                    price=self.last_trade_price
                ) if active_order.qty - qty_to_match != 0 else None
                self.logger.info(f"ROUTE D !!! User {active_order.agent_id}: Order {active_order.order_id} partially/fully executed for {active_order.qty - qty_to_match} shares at {self.last_trade_price}\033[0m")
            else:
                self.logger.error(f"Active order {active_order.order_id} not found in registered users.")


            if qty_to_match != 0:
                # Prepend the remaining order to the sell orders
                active_order.qty = qty_to_match
                self.sell_orders.insert(0, active_order)
                self.sell_orders.sort(key=lambda x: (x.price, x.order_time))
                self.logger.debug(f"Partial match, remaining order: {active_order}, adding to sell orders.")

        
        # Perform global net balance annd net shares check
        init_balance_sum = sum(user.initial_balance for user in self.registered_users.values())
        final_balance_sum = sum(user.balance for user in self.registered_users.values())
        init_shares_sum = sum(user.initial_shares for user in self.registered_users.values())
        final_shares_sum = sum(user.shares for user in self.registered_users.values())
        self.logger.info(f"Global net balance check: Initial: {init_balance_sum}, Final: {final_balance_sum}, Change: {final_balance_sum - init_balance_sum}")
        self.logger.info(f"Global net shares check: Initial: {init_shares_sum}, Final: {final_shares_sum}, Change: {final_shares_sum - init_shares_sum}")
        return matched_orders  # Return matched orders for further processing if needed
    
    def __str__(self):
        # Neatly format the order book for display
        title = " ================Order Book ====================\n"
        title += "Buy Orders:\n"
        header =f"Order ID | Agent ID | Price | Amount\n =====================\n"
        title += header

        for order in self.buy_orders:
            title += f"{order.order_id} | {order.agent_id} | {order.price} | {order.qty}\n"
        ender = "=====================\n"
        title += ender
        title += "\nSell Orders:\n"
        title += header
        for order in self.sell_orders:
            title += f"{order.order_id} | {order.agent_id} | {order.price} | {order.qty}\n"
        title += ender
        title += "=====================================\n"
        title += f"Last Trade Price: {self.last_trade_price}\n"
        title += "=====================================\n"
        return title




    def match_order(self, active_order: Order):
        """Matches an incoming order with existing orders in the order book.
           Only execute the order if completely matched by the opposite order.
        """

        self.logger.debug(f"Book before matching: {self}")
        self.logger.debug(f"Active order: {active_order}")
        active_order.order_time = time.time()  # Set the order time to the current time
        if active_order.order_type == 'buy':
            opposite_orders = self.sell_orders
        else:
            opposite_orders = self.buy_orders

        self.logger.debug(f"Matching order now... {active_order}")

        matched_orders = []
        qty_to_match = active_order.qty
        for order in opposite_orders:
            # Choose by the lowest price for buy orders and highest price for sell orders
            if active_order.order_type == 'buy' and order.price <= active_order.price:
                # Check if the remaining quantity can be matched
                order_cpy = deepcopy(order)
                if qty_to_match > order.qty:
                    qty_to_match -= order.qty
                    # self.last_trade_price = order.price
                    order_cpy.qty = 0
                    order_cpy.filled_qty = order.qty
                    matched_orders.append(order_cpy)
                    self.logger.debug(f"Matched order: {order_cpy} with active order: {active_order}, qty_to_match: {qty_to_match}")
                elif qty_to_match <= order.qty:
                    order_cpy.qty -= qty_to_match
                    order_cpy.filled_qty = qty_to_match
                    matched_orders.append(order_cpy)
                    # self.last_trade_price = order.price
                    qty_to_match = 0
                    self.logger.debug(f"Matched order: {order_cpy} with active order: {active_order}, qty_to_match: {qty_to_match}")
                    self.logger.info(f"Active order was fully matched: {active_order} with orders, proceeding to process matched orders.")
                    break

            elif active_order.order_type == "buy" and order.price > active_order.price:
                # No more matches possible, break the loop
                self.logger.debug(f"No more matches possible for active order: {active_order}.")
                break
                
            elif active_order.order_type == 'sell' and order.price >= active_order.price:
                # Check if the remaining quantity can be matched
                order_cpy = deepcopy(order)
                if qty_to_match > order.qty:
                    qty_to_match -= order.qty
                    # self.last_trade_price = order.price
                    order_cpy.qty = 0
                    order_cpy.filled_qty = order.qty
                    matched_orders.append(order_cpy)
                    self.logger.debug(f"Matched order: {order_cpy} with active order: {active_order}, qty_to_match: {qty_to_match}")
                elif qty_to_match <= order.qty:
                    order_cpy.qty -= qty_to_match
                    # self.last_trade_price = order.price
                    order_cpy.filled_qty = qty_to_match
                    matched_orders.append(order_cpy)
                    qty_to_match = 0
                    self.logger.debug(f"Matched order: {order_cpy} with active order: {active_order}, qty_to_match: {qty_to_match}")
                    self.logger.info(f"Active order was fully matched: {active_order} with orders, proceeding to process matched orders.")
                    break

            elif active_order.order_type == "sell" and order.price < active_order.price:
                # No more matches possible, break the loop
                self.logger.debug(f"No more matches possible for active order: {active_order}.")
                break
        
            else:
                raise ValueError("Invalid order type.")
        
        self.process_matched_orders(matched_orders, active_order, qty_to_match)

        self.logger.debug(f"Book after matching: {self}")
        self.logger.debug(f"Matched orders: {matched_orders}")
        self.logger.info(f"Active order after matching: {active_order}")


        return matched_orders



                    


    def add_order(self, order):
        order.order_time = time.time()
        matched_orders = self.match_order(order)
        return {"status": "success", "message": f"Order {order.order_id} added.", "matched_orders": matched_orders}
        

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            return {"status": "success", "message": f"Order {order_id} canceled."}
        else:
            return {"status": "error", "message": f"Order {order_id} not found."}

    def get_orders(self):
        return self.orders

