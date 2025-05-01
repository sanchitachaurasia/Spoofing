import random
import time, logging
from order_book import OrderBook, User
from typing import List

def setup_logger(filename='order_book_simulation.log', mode='w', level=logging.INFO):
    """Configure logger to write only to file, clearing it first"""
    logger = logging.getLogger('OrderBookSimulator')
    logger.handlers.clear()
    
    # Configure file handler to overwrite (not append)
    file_handler = logging.FileHandler(filename, mode=mode)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.setLevel(level)
    logger.propagate = False
    
    logger.info("Simulation logger initialized - file cleared and ready for new logs")
    return logger

def run_simulation(num_users: int = 5, num_transactions: int = 100):
    """Run a market simulation with K users and N transactions"""
    logger = setup_logger(level=logging.DEBUG)

    order_book = OrderBook(logger=logger)
    
    # Create users with random initial balances and shares
    users: List[User] = []
    for i in range(1, num_users + 1):
        balance = random.randint(50000, 200000)
        shares = random.randint(50, 200)
        user = User(f"User_{i}", balance, shares, logger)
        users.append(user)
        order_book.register_user(user)
        logger.info(f"Created {user.user_id} with ${balance} balance and {shares} shares")

    logger.info(f"\nStarting simulation with {num_users} users and {num_transactions} transactions\n")
    
    # Run the simulation
    for t in range(num_transactions):
        logger.info(f"\n=== Transaction {t+1}/{num_transactions} ===")
        
        # Select random user
        user = random.choice(users)
        
        # Generate order
        current_price = order_book.last_trade_price or 100  # Default to 100 if no trades yet
        order = user.generate_order(current_price)
        
        if order:
            logger.info(f"{user.user_id} generated: {order}")
            result = order_book.add_order(order)
            
            # Log order book state periodically
            if (t+1) % 10 == 0:
                logger.info(f"\nOrder Book State after {t+1} transactions:")
                logger.info(str(order_book))
        
        # Small delay to make logs readable
        time.sleep(0.1)
    
    # Final state
    logger.info("\n=== Simulation Complete ===")
    logger.info("\nFinal Order Book State:")
    logger.info(str(order_book))
    
    logger.info("\nFinal User Balances:")
    for user in users:
        logger.info(f"{user.user_id}: ${user.balance:.2f} balance, {user.shares} shares")

    # Sanity check: Initial shares and balances in the total economy should be the same
    total_initial_balance = sum(user.initial_balance for user in users)
    total_final_balance = sum(user.balance for user in users)
    total_initial_shares = sum(user.initial_shares for user in users)
    total_final_shares = sum(user.shares for user in users)

    logger.info(f"\nTotal Initial Balance: ${total_initial_balance:.2f}, Total Final Balance: ${total_final_balance:.2f}")
    logger.info(f"Total Initial Shares: {total_initial_shares}, Total Final Shares: {total_final_shares}")
    logger.info(f"Balance Change: ${total_final_balance - total_initial_balance:.2f}")
    

    print(f"Simulation complete. Check 'order_book_simulation.log' for details")

if __name__ == "__main__":
    # Example: 5 users, 50 transactions
    run_simulation(num_users=7, num_transactions=50)