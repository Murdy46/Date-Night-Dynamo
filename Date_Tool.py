import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import csv
import random
import os
import sys

# --- THEME COLORS ---
BG_COLOR = "#121212"      
CARD_COLOR = "#1E1E1E"    
ACCENT_COLOR = "#00F2FF"  
TEXT_COLOR = "#FFFFFF"    
SUB_TEXT = "#B0B0B0"      

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "activities.csv")

class DateDynamo:
    def __init__(self, root):
        self.root = root
        self.root.title("DATE NIGHT DYNAMO")
        self.root.geometry("500x850")
        self.root.configure(bg=BG_COLOR)

        self.title_font = ("Segoe UI", 18, "bold")
        self.label_font = ("Segoe UI", 10, "bold")
        self.main_font = ("Segoe UI", 10)

        # Header
        header_frame = tk.Frame(root, bg=BG_COLOR, pady=20)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="DATE NIGHT DYNAMO", font=self.title_font, fg=ACCENT_COLOR, bg=BG_COLOR).pack()
        tk.Label(header_frame, text="PLAN THE NEXT ADVENTURE", font=("Segoe UI", 8), fg=SUB_TEXT, bg=BG_COLOR).pack()

        # Input Card
        input_card = tk.Frame(root, bg=CARD_COLOR, padx=20, pady=20)
        input_card.pack(padx=20, pady=10, fill="x")

        # 1. Date
        self.create_label(input_card, "PICK A DATE")
        self.cal = DateEntry(input_card, width=20, background=ACCENT_COLOR, foreground='black', borderwidth=0, font=self.main_font)
        self.cal.pack(pady=(0, 15))

        # 2. Duration
        self.create_label(input_card, "MAX TIME AVAILABLE")
        self.dur_options = ["<4hr", "<24hrs", "<48hrs", "<7days"]
        self.dur_var = tk.StringVar(value=self.dur_options[0])
        self.dur_drop = ttk.OptionMenu(input_card, self.dur_var, self.dur_options[0], *self.dur_options)
        self.dur_drop.pack(pady=(0, 15), fill="x")

        # 3. Categories (Vibes) - UPDATED TO CHECKBOXES
        self.create_label(input_card, "SELECT VIBES")
        
        # Scrollable container for checkboxes
        self.cat_frame = tk.Frame(input_card, bg="#2A2A2A", pady=5)
        self.cat_frame.pack(fill="x", pady=(0, 10))
        
        self.cat_vars = {} # Stores the True/False status of each vibe
        self.refresh_categories()

        # Generate Button
        self.gen_btn = tk.Button(root, text="GENERATE SURPRISE SCHEDULE", command=self.run_randomizer, 
                                 bg=ACCENT_COLOR, fg="black", font=("Segoe UI", 11, "bold"), 
                                 activebackground="#00B8C4", borderwidth=0, cursor="hand2")
        self.gen_btn.pack(pady=20, padx=40, fill="x")

        # Result Card
        self.res_card = tk.LabelFrame(root, text=" THE PLAN ", bg=BG_COLOR, fg=ACCENT_COLOR, 
                                      font=self.label_font, labelanchor="n", padx=15, pady=15)
        self.res_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.res_display = tk.Text(self.res_card, bg=BG_COLOR, fg=TEXT_COLOR, borderwidth=0, 
                                   font=("Segoe UI", 11), height=10, state="disabled", wrap="word")
        self.res_display.pack(fill="both", expand=True)

    def create_label(self, parent, text):
        lbl = tk.Label(parent, text=text, font=self.label_font, fg=SUB_TEXT, bg=CARD_COLOR)
        lbl.pack(anchor="w", pady=(5, 2))

    def refresh_categories(self):
        """Creates a sleek checkbox for every category found in the CSV"""
        if not os.path.exists(FILE_NAME): return
        
        # Clear existing checkboxes if any
        for widget in self.cat_frame.winfo_children():
            widget.destroy()

        try:
            with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                cats = sorted(list(set(row['Category'] for row in reader if row['Category'])))
                
                for c in cats:
                    var = tk.BooleanVar(value=True) # Default to selected
                    self.cat_vars[c] = var
                    cb = tk.Checkbutton(self.cat_frame, text=c, variable=var, 
                                        bg="#2A2A2A", fg=TEXT_COLOR, 
                                        selectcolor="#121212", # Box interior color
                                        activebackground=ACCENT_COLOR,
                                        font=("Segoe UI", 9), anchor="w")
                    cb.pack(fill="x", padx=10)
        except Exception as e:
            print(f"Error loading categories: {e}")

    def get_season(self, date_obj):
        m = date_obj.month
        if 3 <= m <= 5: return "Spring"
        if 6 <= m <= 8: return "Summer"
        if 9 <= m <= 11: return "Autumn"
        return "Winter"

    def run_randomizer(self):
        if not os.path.exists(FILE_NAME):
            messagebox.showerror("Error", "CSV File Missing!")
            return

        target_season = self.get_season(self.cal.get_date())
        max_dur_idx = self.dur_options.index(self.dur_var.get())
        allowed_durations = self.dur_options[:max_dur_idx+1]
        
        # Get all categories where the checkbox is checked
        selected_cats = [cat for cat, var in self.cat_vars.items() if var.get()]

        if not selected_cats:
            messagebox.showinfo("Wait...", "Please select at least one vibe!")
            return

        with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as f:
            data = list(csv.DictReader(f))

        filtered = [r for r in data if 
                    (r['Season'] == "Any" or r['Season'] == target_season) and 
                    (r['Duration'] in allowed_durations) and 
                    (r['Category'] in selected_cats)]

        if not filtered:
            messagebox.showinfo("Wait...", "Nothing fits! Try selecting more vibes or a longer duration.")
            return

        count = 2 if (max_dur_idx > 0 and len(filtered) > 1) else 1
        selections = random.sample(filtered, count)
        
        self.res_display.config(state="normal")
        self.res_display.delete('1.0', tk.END)
        for i, item in enumerate(selections, 1):
            self.res_display.insert(tk.END, f"★ {item['Activity'].upper()}\n")
            self.res_display.insert(tk.END, f"   {item['Category']} | {item['Cost']} | {item['Duration']}\n")
            if item['Comments']:
                self.res_display.insert(tk.END, f"   Note: {item['Comments']}\n")
            self.res_display.insert(tk.END, "\n")
        self.res_display.config(state="disabled")

        if messagebox.askyesno("CONFIRM DATE?", "Lock this in? These will be removed from your list."):
            self.remove_from_csv([s['Activity'] for s in selections])
            self.res_display.config(state="normal")
            self.res_display.insert(tk.END, "LOCKED IN. HAVE A GREAT TIME! 🔥")
            self.res_display.config(state="disabled")

    def remove_from_csv(self, names):
        with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = [r for r in reader if r['Activity'] not in names]
        with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

if __name__ == "__main__":
    root = tk.Tk()
    app = DateDynamo(root)
    root.mainloop()