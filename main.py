import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from datetime import datetime
import json, os

try:
    from ics import Calendar
except ImportError:
    Calendar = None
    print("The 'ics' package is not installed. Install with: pip install ics")


SAVE_FILE = "planner_data.json"


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Planner")

        # Data structures
        self.todo_lists = {}
        self.current_list = None

        # === TO-DO LIST SECTION ===
        tk.Label(root, text="To-Do Lists", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5)

        self.listbox_lists = tk.Listbox(root, height=5, width=30)
        self.listbox_lists.grid(row=1, column=0, padx=5)
        self.listbox_lists.bind("<<ListboxSelect>>", self.select_list)

        self.entry_new_list = tk.Entry(root, width=20)
        self.entry_new_list.grid(row=2, column=0, padx=5, pady=5)
        tk.Button(root, text="Add List", command=self.add_list).grid(row=3, column=0, pady=5)

        self.label_current_list = tk.Label(root, text="Current List: None", font=("Arial", 10, "italic"))
        self.label_current_list.grid(row=4, column=0, pady=5)

        self.listbox_tasks = tk.Listbox(root, height=10, width=50)
        self.listbox_tasks.grid(row=5, column=0, padx=5)

        self.entry_task = tk.Entry(root, width=30)
        self.entry_task.grid(row=6, column=0, padx=5, pady=5)

        tk.Button(root, text="Add Task", command=self.add_task).grid(row=7, column=0, pady=5)
        tk.Button(root, text="Mark Completed", command=self.mark_completed).grid(row=8, column=0, pady=5)

        # === MEETINGS SECTION ===
        tk.Label(root, text="Meetings", font=("Arial", 14, "bold")).grid(row=0, column=1, pady=5)

        self.meeting_listbox = tk.Listbox(root, height=20, width=50)
        self.meeting_listbox.grid(row=1, column=1, rowspan=6, padx=5)

        tk.Button(root, text="Add Meeting", command=self.add_meeting).grid(row=7, column=1, pady=5)

        # Delete Meeting button
        tk.Button(root, text="Delete Meeting", command=self.delete_meeting).grid(row=8, column=1, pady=5)

        # === IMPORT SECTION ===
        tk.Button(root, text="Import .ics Calendar", command=self.import_ics).grid(row=9, column=1, pady=5)

        # === Load saved data ===
        self.load_data()

        # Save on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- TO-DO FUNCTIONS ---
    def add_list(self):
        name = self.entry_new_list.get().strip()
        if not name:
            messagebox.showwarning("Invalid", "List name cannot be empty.")
            return
        if name in self.todo_lists:
            messagebox.showwarning("Invalid", "List already exists.")
            return
        self.todo_lists[name] = []
        self.listbox_lists.insert(tk.END, name)
        self.entry_new_list.delete(0, tk.END)

    def select_list(self, event=None):
        selection = self.listbox_lists.curselection()
        if not selection:
            return
        self.current_list = self.listbox_lists.get(selection[0])
        self.label_current_list.config(text=f"Current List: {self.current_list}")
        self.update_task_list()

    def update_task_list(self):
        self.listbox_tasks.delete(0, tk.END)
        if self.current_list:
            for task in self.todo_lists[self.current_list]:
                self.listbox_tasks.insert(tk.END, task)

    def add_task(self):
        if not self.current_list:
            messagebox.showwarning("No List", "Please select a to-do list first.")
            return
        task = self.entry_task.get().strip()
        if not task:
            messagebox.showwarning("Invalid", "Task cannot be empty.")
            return
        self.todo_lists[self.current_list].append(task)
        self.entry_task.delete(0, tk.END)
        self.update_task_list()

    def mark_completed(self):
        selection = self.listbox_tasks.curselection()
        if not selection or not self.current_list:
            return
        index = selection[0]
        task = self.todo_lists[self.current_list][index]
        completed_task = f"✓ {task}"
        self.todo_lists[self.current_list][index] = completed_task
        self.update_task_list()

    # --- MEETING FUNCTIONS ---
    def add_meeting(self):
        who = simpledialog.askstring("Meeting", "Who is the meeting with?")
        when = simpledialog.askstring("Meeting", "When is the meeting? (YYYY-MM-DD HH:MM)")
        how = simpledialog.askstring("Meeting", "How will the meeting take place?")

        try:
            datetime.strptime(when, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD HH:MM")
            return

        if who and when and how:
            meeting = f"With {who} on {when} via {how}"
            self.meeting_listbox.insert(tk.END, meeting)

    # Delete meeting method
    def delete_meeting(self):
        selection = self.meeting_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a meeting to delete.")
            return
        self.meeting_listbox.delete(selection[0])

    # --- ICS IMPORT ---
    def import_ics(self):
        if Calendar is None:
            messagebox.showerror("Error", "ICS library not installed. Run: pip install ics")
            return

        filepath = filedialog.askopenfilename(filetypes=[("ICS files", "*.ics")])
        if not filepath:
            return

        with open(filepath, "r", encoding="utf-8") as f:
            c = Calendar(f.read())

        for event in c.events:
            choice = messagebox.askquestion(
                "Import Event",
                f"Event: {event.name}\nDate: {event.begin}\n\n"
                "Would you like to import this as a Meeting?\n"
                "Click 'Yes' for Meeting, 'No' for To-Do."
            )

            if choice == "yes":
                meeting_info = f"{event.name} - {event.begin.format('YYYY-MM-DD HH:mm')}"
                self.meeting_listbox.insert(tk.END, meeting_info)
            else:
                if self.current_list is None:
                    messagebox.showwarning("No List Selected", "Please select a to-do list first.")
                else:
                    self.todo_lists[self.current_list].append(event.name)
                    self.update_task_list()

    # --- SAVE / LOAD FUNCTIONS ---
    def save_data(self):
        data = {
            "todo_lists": self.todo_lists,
            "meetings": list(self.meeting_listbox.get(0, tk.END)),
            "current_list": self.current_list,
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.todo_lists = data.get("todo_lists", {})
                for list_name in self.todo_lists:
                    self.listbox_lists.insert(tk.END, list_name)

                for meeting in data.get("meetings", []):
                    self.meeting_listbox.insert(tk.END, meeting)

                self.current_list = data.get("current_list")
                if self.current_list:
                    self.label_current_list.config(text=f"Current List: {self.current_list}")
                    self.update_task_list()

    def on_close(self):
        self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PlannerApp(root)
    root.mainloop()
