import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import threading
import time

# Database file path
DB_PATH = "food_expiration.db"

# Connects to the SQLite database
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        expiration_date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

class FoodExpirationApp:
    def __init__(self, root):  # Corrected the method name to __init__
        self.root = root
        self.root.title("Food Expiration Tracker")

        # Create and place input fields
        tk.Label(root, text="Food Item Name:").grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Expiration Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.date_entry = tk.Entry(root)
        self.date_entry.grid(row=1, column=1, padx=10, pady=5)

        # Buttons for adding items, checking expiration, and removing items
        add_button = tk.Button(root, text="Add Food Item", command=self.add_food_item)
        add_button.grid(row=2, column=0, columnspan=2, pady=10)

        remove_button = tk.Button(root, text="Remove Selected Item", command=self.remove_selected_item)
        remove_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.item_list = tk.Listbox(root, width=50, height=15)
        self.item_list.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Load items and start the background expiration check
        self.load_items()
        threading.Thread(target=self.start_expiration_check, daemon=True).start()

    # Adds a food item to the database
    def add_food_item(self):
        name = self.name_entry.get().strip()
        expiration_date = self.date_entry.get().strip()

        if not name or not expiration_date:
            messagebox.showwarning("Input Error", "Both fields must be filled out.")
            return

        try:
            datetime.strptime(expiration_date, "%Y-%m-%d")  # Validate date format
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO food_items (name, expiration_date) VALUES (?, ?)", (name, expiration_date))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"{name} added with expiration date {expiration_date}.")
            self.name_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.load_items()
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter the date in YYYY-MM-DD format.")

    # Loads all items from the database and displays them in the list
    def load_items(self):
        self.item_list.delete(0, tk.END)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, expiration_date FROM food_items")
        self.items = cursor.fetchall()
        conn.close()

        for item_id, name, date in self.items:
            self.item_list.insert(tk.END, f"{name} - Expires on: {date}")

    # Checks for items expiring within 3 days and prompts the user
    def check_expirations(self):
        today = datetime.today()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, expiration_date FROM food_items")
        items = cursor.fetchall()
        conn.close()

        for item_id, name, expiration_date in items:
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            days_left = (exp_date - today).days

            if 0 <= days_left <= 3:  # Expiring within 3 days
                self.prompt_remove_item(item_id, name, days_left)

    # Prompts the user to remove an item that's close to expiration
    def prompt_remove_item(self, item_id, name, days_left):
        response = messagebox.askyesno(
            "Expiration Reminder",
            f"{name} expires in {days_left} day(s). Do you want to remove it?"
        )
        if response:
            self.remove_item(item_id)

    # Removes an item from the database by ID
    def remove_item(self, item_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        self.load_items()

    # Manual removal of a selected item from the list
    def remove_selected_item(self):
        selected_index = self.item_list.curselection()
        if not selected_index:
            messagebox.showwarning("No Selection", "Please select an item to remove.")
            return

        selected_text = self.item_list.get(selected_index)
        selected_name = selected_text.split(" - ")[0]  # Extract the item name

        # Find the item ID corresponding to the selected name
        item_id = None
        for id, name, _ in self.items:
            if name == selected_name:
                item_id = id
                break

        if item_id:
            self.remove_item(item_id)
            messagebox.showinfo("Removed", f"{selected_name} has been removed from the database.")
        else:
            messagebox.showerror("Error", "Could not find the selected item in the database.")

    # Runs a daily check for items expiring soon
    def start_expiration_check(self):
        while True:
            self.check_expirations()
            time.sleep(24 * 60 * 60)  # Check once per day

# Setup the database before running the app
setup_database()

# Create and run the main application window
root = tk.Tk()
app = FoodExpirationApp(root)
root.mainloop()
