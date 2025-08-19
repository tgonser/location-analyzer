import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import os
import threading
from datetime import datetime, date
import json
from analyzer_bridge import process_location_file
import pandas as pd

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save config: {e}")

class LocationAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.cancel_requested = threading.Event()
        self.root.title("Google Location Analyzer")
        self.config = load_config()
        self.analysis_running = False
        self.cancel_after_id = None
        self.file_min_date = None
        self.file_max_date = None
        self.toplevel_windows = []
        self.analysis_thread = None
        self.date_parse_thread = None
        self.current_file_path = None

        # Initialize variables (removed output_mode_var)
        self.file_path = tk.StringVar(value=self.config.get("last_input", ""))
        self.output_dir = tk.StringVar(value=self.config.get("last_output", ""))
        self.api_key_geoapify = tk.StringVar(value=self.config.get("geoapify_key", ""))
        self.api_key_google = tk.StringVar(value=self.config.get("google_key", ""))
        self.api_key_onwater = tk.StringVar(value=self.config.get("onwater_key", ""))
        self.delay = tk.DoubleVar(value=self.config.get("delay", 0.5))
        self.batch_size = tk.IntVar(value=self.config.get("batch_size", 1))
        self.max_coords = tk.StringVar(value=str(self.config.get("max_coords", "")))
        self.start_date = tk.StringVar(value=self.config.get("start_date", ""))
        self.end_date = tk.StringVar(value=self.config.get("end_date", ""))

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Load saved dates with error handling
        try:
            if self.config.get("start_date"):
                self.start_picker.set_date(datetime.strptime(self.config["start_date"], "%Y-%m-%d").date())
            else:
                self.start_picker.set_date(date.today())
            if self.config.get("end_date"):
                self.end_picker.set_date(datetime.strptime(self.config["end_date"], "%Y-%m-%d").date())
            else:
                self.end_picker.set_date(date.today())
        except Exception as e:
            self.log(f"Date restore failed: {e}")
            self.start_picker.set_date(date.today())
            self.end_picker.set_date(date.today())

        if self.file_path.get() and self.file_path.get() != self.current_file_path:
            self.current_file_path = self.file_path.get()
            self._start_date_parse_thread(self.file_path.get())

    def _log_to_textbox(self, msg):
        self.output_text.insert("end", msg + "\n")
        self.output_text.see("end")
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass

    def log(self, msg):
        self._log_to_textbox(msg)

    def log_output(self, msg):
        self.log(msg)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.file_path.set(path)
            self.current_file_path = path
            self._start_date_parse_thread(path)
            self.config["last_input"] = path
            save_config(self.config)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)
            self.config["last_output"] = path
            save_config(self.config)

    def _save_api_keys(self, *args):
        """Save API keys to config when modified."""
        self.config["geoapify_key"] = self.api_key_geoapify.get()
        self.config["google_key"] = self.api_key_google.get()
        self.config["onwater_key"] = self.api_key_onwater.get()
        save_config(self.config)

    def _start_date_parse_thread(self, file_path):
        self.file_range_label.config(text="File range: Loading file dates...")
        self.root.update_idletasks()
        self.date_parse_thread = threading.Thread(target=self._display_file_date_range, args=(file_path,))
        self.date_parse_thread.daemon = True
        self.date_parse_thread.start()

    def _display_file_date_range(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            dates = []
            timeline_objects = data.get("timelineObjects", data) if isinstance(data, dict) else data
            for obj in timeline_objects:
                if self.cancel_requested.is_set():
                    self.root.after(0, self._update_file_range_label, "File range: Parsing canceled")
                    self.root.after(0, self.log, "❌ Date parsing canceled")
                    return
                start_str = obj.get("startTime")
                if start_str:
                    try:
                        dt = pd.to_datetime(start_str, utc=True).date()
                        dates.append(dt)
                    except Exception:
                        continue
            if dates:
                self.file_min_date = min(dates)
                self.file_max_date = max(dates)
                self.root.after(0, self._update_file_range_label,
                                f"File range: {self.file_min_date} to {self.file_max_date}")
                self.root.after(0, self.log, f"Loaded file date range: {self.file_min_date} to {self.file_max_date}")
            else:
                self.file_min_date = None
                self.file_max_date = None
                self.root.after(0, self._update_file_range_label, "File range: No valid dates found")
                self.root.after(0, self.log, "No valid dates found in file")
        except Exception as e:
            self.file_min_date = None
            self.file_max_date = None
            self.root.after(0, self._update_file_range_label, "File range: Error loading dates")
            self.root.after(0, self.log, f"❌ Error loading file dates: {e}")
        finally:
            self.date_parse_thread = None

    def _update_file_range_label(self, text):
        try:
            self.file_range_label.config(text=text)
            self.root.update_idletasks()
        except tk.TclError:
            pass

    def _save_dates(self, event=None):
        try:
            self.config["start_date"] = str(self.start_picker.get_date())
            self.config["end_date"] = str(self.end_picker.get_date())
            self.config["onwater_key"] = self.api_key_onwater.get()
            save_config(self.config)
        except Exception as e:
            self.log(f"❌ Error saving dates or API keys: {e}")

    def start_and_run(self):
        if self.analysis_running:
            self.log("⚠️ Analysis already running. Please wait or cancel.")
            return
        start_date = self.start_picker.get_date()
        end_date = self.end_picker.get_date()
        if self.file_min_date and self.file_max_date:
            if start_date < self.file_min_date or end_date > self.file_max_date:
                response = messagebox.askyesno(
                    "Date Range Warning",
                    f"Selected dates ({start_date} to {end_date}) are outside the file's data range "
                    f"({self.file_min_date} to {self.file_max_date}). This may result in no data. Continue?"
                )
                if not response:
                    return
        self._save_dates()
        self.start_analysis()
        self.log(f"Parsing from {start_date} to {end_date}")
        self.run_analysis()

    def cancel_analysis(self):
        self.cancel_flag = True
        self.cancel_requested.set()
        self.log("❌ Cancel requested...")
        self.cancel_after_id = self.root.after(1000, self._confirm_cancel)

    def _confirm_cancel(self):
        if not self.analysis_running:
            self.log("✅ Cancellation complete.")
            self.cancel_after_id = None
        else:
            self.cancel_after_id = self.root.after(1000, self._confirm_cancel)

    def start_analysis(self):
        self.cancel_flag = False
        self.cancel_requested.clear()
        if self.cancel_after_id:
            self.root.after_cancel(self.cancel_after_id)
            self.cancel_after_id = None
        self.output_text.delete("1.0", tk.END)
        self.analysis_running = True

    def run_analysis(self):
        file_path = self.file_path.get()
        start_date = self.start_picker.get_date()
        end_date = self.end_picker.get_date()
        output_dir = self.output_dir.get()
        
        # Always use "by_city" since we generate all files anyway
        group_by = "by_city"
        
        geoapify_key = self.api_key_geoapify.get()
        google_key = self.api_key_google.get()
        onwater_key = self.api_key_onwater.get()
        delay = float(self.delay.get())
        batch_size = int(self.batch_size.get())
        args = (
            file_path,
            start_date,
            end_date,
            output_dir,
            group_by,
            geoapify_key,
            google_key,
            onwater_key,
            delay,
            batch_size,
            self.log_output,
            self.cancel_requested.is_set,
        )
        self.config["onwater_key"] = onwater_key
        save_config(self.config)
        self.analysis_thread = threading.Thread(target=self._run_analysis_thread, args=args)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def _run_analysis_thread(self, *args):
        try:
            process_location_file(*args)
            self.root.after(0, self.log, "✅ Analysis complete. All CSV files generated successfully.")
        except Exception as e:
            self.root.after(0, self.log, f"❌ Analysis failed: {e}")
        finally:
            self.root.after(0, self._finish_analysis)

    def _finish_analysis(self):
        self.analysis_running = False
        self.analysis_thread = None

    def quit_app(self):
        self.cancel_requested.set()
        if self.analysis_running:
            self.cancel_flag = True
            self.log("❌ Terminating analysis...")
        if self.date_parse_thread:
            self.log("❌ Terminating date parsing...")
        for window in self.toplevel_windows:
            try:
                window.destroy()
            except:
                pass
        self.config["onwater_key"] = self.api_key_onwater.get()
        save_config(self.config)
        self.root.destroy()

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input file
        ttk.Label(main_frame, text="Input JSON:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=2)

        # Output dir
        ttk.Label(main_frame, text="Output Dir:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=5, pady=2)

        # Dates
        ttk.Label(main_frame, text="Start Date:").grid(row=2, column=0, sticky="w", pady=2)
        self.start_picker = DateEntry(main_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_picker.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.start_picker.bind("<<DateEntrySelected>>", self._save_dates)

        ttk.Label(main_frame, text="End Date:").grid(row=3, column=0, sticky="w", pady=2)
        self.end_picker = DateEntry(main_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_picker.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.end_picker.bind("<<DateEntrySelected>>", self._save_dates)

        # File range label
        self.file_range_label = ttk.Label(main_frame, text="File range: Select a file")
        self.file_range_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=2)

        # API keys
        ttk.Label(main_frame, text="Geoapify Key:").grid(row=5, column=0, sticky="w", pady=2)
        geoapify_entry = ttk.Entry(main_frame, textvariable=self.api_key_geoapify, width=50)
        geoapify_entry.grid(row=5, column=1, padx=5, pady=2)
        geoapify_entry.bind("<FocusOut>", self._save_api_keys)

        ttk.Label(main_frame, text="Google Key:").grid(row=6, column=0, sticky="w", pady=2)
        google_entry = ttk.Entry(main_frame, textvariable=self.api_key_google, width=50)
        google_entry.grid(row=6, column=1, padx=5, pady=2)
        google_entry.bind("<FocusOut>", self._save_api_keys)

        ttk.Label(main_frame, text="OnWater Key (RapidAPI):").grid(row=7, column=0, sticky="w", pady=2)
        onwater_entry = ttk.Entry(main_frame, textvariable=self.api_key_onwater, width=50)
        onwater_entry.grid(row=7, column=1, padx=5, pady=2)
        onwater_entry.bind("<FocusOut>", self._save_api_keys)

        # Other settings
        ttk.Label(main_frame, text="API Delay (s):").grid(row=8, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.delay, width=10).grid(row=8, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(main_frame, text="Batch Size:").grid(row=9, column=0, sticky="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.batch_size, width=10).grid(row=9, column=1, sticky="w", padx=5, pady=2)

        # Removed Output Mode section completely

        # Button frame
        button_frame = ttk.Frame(self.root, padding=5)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Run Analysis", command=self.start_and_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Quit", command=self.quit_app).pack(side=tk.LEFT, padx=5)

        # Output text
        self.output_text = tk.Text(self.root, height=10, width=80)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    print("🚀 Starting LocationAnalyzerApp initialization")
    root = tk.Tk()
    app = LocationAnalyzerApp(root)
    root.mainloop()
