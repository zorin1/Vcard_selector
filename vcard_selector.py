#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class VCFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VCF Contact Manager")

        self.contacts = []
        self.check_vars = []
        self.selection_states = {}
        self.show_selected_only = False

        self.create_widgets()
        self.bind_scroll_events()

    def create_widgets(self):
        # Top frame for load button and controls
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        self.load_btn = ttk.Button(top_frame, text="Load VCF File", command=self.load_vcf)
        self.load_btn.pack(side=tk.LEFT)

        # Control buttons on the right
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(side=tk.RIGHT)

        self.sort_toggle_var = tk.BooleanVar(value=True)
        self.sort_toggle = ttk.Checkbutton(control_frame, text="Sort", variable=self.sort_toggle_var, command=self.toggle_sort_order)
        self.sort_toggle.pack(side=tk.LEFT, padx=5)

        self.show_selected_var = tk.BooleanVar()
        self.show_selected_toggle = ttk.Checkbutton(control_frame, text="Show Selected Only", variable=self.show_selected_var, command=self.toggle_show_selected)
        self.show_selected_toggle.pack(side=tk.LEFT)

        # Middle frame with scrollable checkboxes
        mid_frame = ttk.Frame(self.root, borderwidth=2, relief="solid")
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(mid_frame)
        self.scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.inner_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.select_all_btn = ttk.Button(btn_frame, text="Select All", command=self.select_all)
        self.select_all_btn.pack(side=tk.LEFT)

        self.unselect_all_btn = ttk.Button(btn_frame, text="Unselect All", command=self.unselect_all)
        self.unselect_all_btn.pack(side=tk.LEFT, padx=5)

        # Export and counter
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self.export_btn = ttk.Button(bottom_frame, text="Export Selected", command=self.export_selected)
        self.export_btn.pack(side=tk.LEFT)

        self.counter_label = ttk.Label(bottom_frame, text="Total: 0 | Selected: 0", anchor="e")
        self.counter_label.pack(side=tk.RIGHT, padx=10)

    def bind_scroll_events(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        # Only scroll if there's content to scroll
        if self.scrollable_frame.winfo_height() > self.canvas.winfo_height():
            if event.num == 4:  # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                self.canvas.yview_scroll(1, "units")
            else:  # Windows/macOS
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_vcf(self):
        filepath = filedialog.askopenfilename(filetypes=[("VCF files", "*.vcf")])
        if not filepath:
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        entries = []
        raw_entries = content.split('BEGIN:VCARD')
        for entry in raw_entries[1:]:
            entry = entry.strip()
            if 'END:VCARD' in entry:
                vcard_data = 'BEGIN:VCARD\n' + entry.split('END:VCARD')[0] + 'END:VCARD'
                entries.append(vcard_data)

        self.contacts.clear()
        self.selection_states.clear()

        for index, data in enumerate(entries):
            fn = 'Unnamed Contact'
            for line in data.split('\n'):
                if line.startswith('FN:'):
                    fn = line[3:].strip()
                    break
            self.contacts.append({'fn': fn, 'original_index': index, 'data': data})

        if self.sort_toggle_var.get():
            self.contacts.sort(key=lambda x: x['fn'].lower())
        self.redraw_checkboxes()

    def redraw_checkboxes(self):
        # Clear existing checkboxes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.check_vars = []
        filtered_contacts = self.contacts if not self.show_selected_only else [
            c for c in self.contacts
            if self.selection_states.get(c['original_index'], False)
        ]

        # Create new checkboxes
        for contact in filtered_contacts:
            var = tk.BooleanVar(value=self.selection_states.get(contact['original_index'], False))

            cb = ttk.Checkbutton(
                self.scrollable_frame,
                text=contact['fn'],
                variable=var,
                command=self.update_counter
            )
            var.trace_add('write',
                lambda *args, k=contact['original_index'], v=var: self.selection_states.update({k: v.get()}))

            cb.pack(anchor=tk.W, fill=tk.X)
            self.check_vars.append(var)

        # Update UI elements
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0.0)
        self.canvas.itemconfig(self.inner_frame_id, width=self.canvas.winfo_width())
        self.update_counter()

    def toggle_sort_order(self):
        if self.sort_toggle_var.get():
            self.contacts.sort(key=lambda x: x['fn'].lower())
        else:
            self.contacts.sort(key=lambda x: x['original_index'])
        self.redraw_checkboxes()

    def toggle_show_selected(self):
        self.show_selected_only = self.show_selected_var.get()
        self.redraw_checkboxes()

    def select_all(self):
        for contact in self.contacts:
            self.selection_states[contact['original_index']] = True
        self.redraw_checkboxes()

    def unselect_all(self):
        for contact in self.contacts:
            self.selection_states[contact['original_index']] = False
        self.redraw_checkboxes()

    def update_counter(self):
        total = len(self.contacts)
        selected = sum(self.selection_states.values())
        self.counter_label.config(text=f"Total: {total} | Selected: {selected}")

    def export_selected(self):
        selected_indices = [k for k, v in self.selection_states.items() if v]
        if not selected_indices:
            messagebox.showwarning("No Selection", "No contacts selected for export.")
            return

        selected_data = []
        for contact in sorted(self.contacts, key=lambda x: x['original_index']):
            if contact['original_index'] in selected_indices:
                selected_data.append(contact['data'])

        save_path = filedialog.asksaveasfilename(defaultextension=".vcf", filetypes=[("VCF files", "*.vcf")])
        if not save_path:
            return

        with open(save_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('\n'.join(selected_data) + '\n')

        messagebox.showinfo("Success", f"Exported {len(selected_data)} contacts to {save_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = VCFApp(root)
    root.mainloop()
