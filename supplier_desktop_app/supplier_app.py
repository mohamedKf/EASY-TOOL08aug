import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import webbrowser



# ---------------- CONFIG ----------------
API_URL = "http://127.0.0.1:8000"   # <— change if your Django runs elsewhere

# Light palette: soft white + light gray
COLORS = {
    "bg": "#F5F7FA",       # app background (very light gray)
    "card": "#FFFFFF",     # cards / panels (white)
    "elev": "#EEF1F6",     # subtle elevated background (light gray)
    "fg": "#111317",       # main text (near black)
    "muted": "#6B7280",    # muted text (cool gray)
    "line": "#DADDE5",     # hairline separators
    "blue": "#1877F2",     # Facebook blue (primary)
    "blue_hover": "#3A8CFF",
    "red": "#E63946",      # accent red
    "row_alt": "#F3F5F9",  # zebra alt row
}

FONT_BASE = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI Semibold", 18)
FONT_SUB = ("Segoe UI", 12)

PADX = 22
PADY = 14


# ---------------- API CLIENT ----------------
class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()

    def supplier_login(self, username: str, password: str):
        r = self.s.post(f"{self.base_url}/api/supplier/login/",
                        json={"username": username, "password": password}, timeout=10)
        if r.status_code != 200:
            try:
                msg = r.json().get("message", f"HTTP {r.status_code}")
            except Exception:
                msg = f"HTTP {r.status_code}"
            raise ValueError(msg)
        return r.json()

    def get_orders(self):
        r = self.s.get(f"{self.base_url}/api/supplier/orders/", timeout=10)
        r.raise_for_status()
        return r.json()

    def update_order(self, order_id: int, status: str = None, delivery_date: str = None):
        payload = {}
        if status:
            payload["status"] = status
        if delivery_date:
            payload["delivery_date"] = delivery_date
        r = self.s.put(
            f"{self.base_url}/api/supplier/orders/{order_id}/update/",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def get_supplier_inventory(self):
        """
        GET supplier inventory.
        Expects: {"status":"ok","inventory": {...}}
        """
        # Prefer the REST-y path to match your other endpoints:
        url = f"{self.base_url}/api/supplier/inventory/"

        # If your server view is currently mounted at /api_supplier_inventory,
        # switch the line above to:
        # url = f"{self.base_url}/api_supplier_inventory"

        r = self.s.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def add_screw(self, screw_type: str, length_cm: float, count_per_box: int, price_per_100: float):
        return self._post("/api/supplier/inventory/screws/add/", {
            "screw_type": screw_type, "length_cm": length_cm,
            "count_per_box": count_per_box, "price_per_100": price_per_100
        })

    def add_profile_set(self, aluminum_profile_id: int, kind: str, name: str, code_string: str,
                        set_code: int, weight_per_meter: float, price_per_kilo: float):
        return self._post("/api/supplier/inventory/profile-sets/add/", {
            "aluminum_profile": aluminum_profile_id,  # FK field name on the form/model
            "kind": kind, "name": name, "code_string": code_string,
            "set_code": set_code, "weight_per_meter": weight_per_meter, "price_per_kilo": price_per_kilo
        })

    def add_metal_profile(self, profile_type: str, size: str, length_meters: float, quantity: int,
                          price_per_piece: float):
        return self._post("/api/supplier/inventory/metal-profiles/add/", {
            "profile_type": profile_type, "size": size, "length_meters": length_meters,
            "quantity": quantity, "price_per_piece": price_per_piece
        })

    def add_drywall_board(self, color: str, size: str, thickness_mm: int, quantity: int, price_per_board: float):
        return self._post("/api/supplier/inventory/drywall-boards/add/", {
            "color": color, "size": size, "thickness_mm": thickness_mm,
            "quantity": quantity, "price_per_board": price_per_board
        })

    # helper:
    def _post(self, path, payload):
        r = self.s.post(f"{self.base_url}{path}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def edit_screw(self, screw_id: int, data: dict):
        r = self.s.put(
            f"{self.base_url}/api/supplier/inventory/screws/{screw_id}/edit/",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def delete_screw(self, screw_id: int):
        r = self.s.delete(
            f"{self.base_url}/api/supplier/inventory/screws/{screw_id}/delete/",
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    # --- Profile Sets ---
    def edit_profile_set(self, ps_id: int, data: dict):
        r = self.s.put(
            f"{self.base_url}/api/supplier/inventory/profile-sets/{ps_id}/edit/",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def delete_profile_set(self, ps_id: int):
        r = self.s.delete(
            f"{self.base_url}/api/supplier/inventory/profile-sets/{ps_id}/delete/",
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    # --- Metal Profiles ---
    def edit_metal_profile(self, mp_id: int, data: dict):
        r = self.s.put(
            f"{self.base_url}/api/supplier/inventory/metal-profiles/{mp_id}/edit/",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def delete_metal_profile(self, mp_id: int):
        r = self.s.delete(
            f"{self.base_url}/api/supplier/inventory/metal-profiles/{mp_id}/delete/",
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    # --- Drywall Boards ---
    def edit_drywall_board(self, db_id: int, data: dict):
        r = self.s.put(
            f"{self.base_url}/api/supplier/inventory/drywall-boards/{db_id}/edit/",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def delete_drywall_board(self, db_id: int):
        r = self.s.delete(
            f"{self.base_url}/api/supplier/inventory/drywall-boards/{db_id}/delete/",
            timeout=10
        )
        r.raise_for_status()
        return r.json()


# ---------------- THEME ----------------
def apply_light_style(root: tk.Tk):
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")

    # Base
    style.configure(".", font=FONT_BASE, foreground=COLORS["fg"], background=COLORS["bg"])

    # Frames / headers / cards
    style.configure("Header.TFrame", background=COLORS["bg"])
    style.configure("CardOuter.TFrame", background=COLORS["elev"], relief="flat")
    style.configure("CardInner.TFrame", background=COLORS["card"], relief="flat")

    # Labels
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])

    # Entry
    style.configure("TEntry",
                    fieldbackground=COLORS["card"],
                    foreground=COLORS["fg"],
                    bordercolor=COLORS["line"])
    style.map("TEntry",
              bordercolor=[("focus", COLORS["blue"])],
              lightcolor=[("focus", COLORS["blue"])])

    # Buttons
    style.configure("Primary.TButton",
                    background=COLORS["blue"], foreground="white",
                    borderwidth=0, padding=(14, 9))
    style.map("Primary.TButton", background=[("active", COLORS["blue_hover"])])

    style.configure("Ghost.TButton",
                    background=COLORS["card"], foreground=COLORS["fg"],
                    borderwidth=0, padding=(12, 8))
    style.map("Ghost.TButton", background=[("active", COLORS["elev"])])

    style.configure("Danger.TButton",
                    background=COLORS["red"], foreground="white",
                    borderwidth=0, padding=(14, 9))

    # Combobox
    style.configure("TCombobox",
                    fieldbackground=COLORS["card"],
                    background=COLORS["card"],
                    foreground=COLORS["fg"])
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["card"])],
              foreground=[("readonly", COLORS["fg"])])

    # Treeview
    style.configure("Treeview",
                    background=COLORS["card"],
                    fieldbackground=COLORS["card"],
                    foreground=COLORS["fg"],
                    rowheight=28,
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=COLORS["elev"],
                    foreground=COLORS["fg"],
                    relief="flat")
    style.map("Treeview.Heading", background=[("active", COLORS["elev"])])


def accent_bar(parent):
    bar = tk.Frame(parent, bg=COLORS["blue"], height=3)
    bar.pack(fill="x", side="top")
    return bar


def card(parent, padx=PADX, pady=PADY):
    # outer (elevated bg)
    outer = ttk.Frame(parent, style="CardOuter.TFrame")
    outer.pack(fill="x", padx=PADX, pady=PADY)
    # inner (white card)
    inner = ttk.Frame(outer, style="CardInner.TFrame")
    inner.pack(fill="both", expand=True, padx=16, pady=16)
    return inner


def center(win, w, h):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = int((sw - w) / 2), int((sh - h) / 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


# ---------------- WINDOWS ----------------
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supplier — Sign in")
        self.resizable(False, False)
        apply_light_style(self)
        accent_bar(self)
        center(self, 480, 380)

        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x", padx=PADX, pady=(PADY, 6))
        ttk.Label(header, text="Supplier Login", font=FONT_TITLE).pack(anchor="w")
        ttk.Label(header, text="Sign in to manage your orders", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        form = card(self)
        ttk.Label(form, text="Username", background=COLORS["card"]).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.username = ttk.Entry(form, width=36)
        self.username.grid(row=1, column=0, sticky="we", pady=(0, 12))

        ttk.Label(form, text="Password", background=COLORS["card"]).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.password = ttk.Entry(form, show="•", width=36)
        self.password.grid(row=3, column=0, sticky="we")

        actions = ttk.Frame(self, style="Header.TFrame")
        actions.pack(fill="x", padx=PADX, pady=(8, PADY))
        self.login_btn = ttk.Button(actions, text="Login", style="Primary.TButton", command=self.do_login)
        self.login_btn.pack(side="left")
        ttk.Button(actions, text="Sign up (website)", style="Ghost.TButton",
                   command=lambda: webbrowser.open(f"{API_URL}/signup/")).pack(side="right")

        self.status = ttk.Label(self, text="", style="Muted.TLabel")
        self.status.pack(anchor="w", padx=PADX, pady=(0, PADY // 2))

        self.api = ApiClient(API_URL)
        self.bind("<Return>", lambda _e: self.do_login())

    def set_status(self, msg):
        self.status.config(text=msg)

    def do_login(self):
        u, p = self.username.get().strip(), self.password.get().strip()
        if not u or not p:
            messagebox.showerror("Missing info", "Please enter both username and password.")
            return
        self.login_btn.config(state="disabled")
        self.set_status("Signing in…")
        self.after(50, self._login_async, u, p)

    def _login_async(self, u, p):
        try:
            data = self.api.supplier_login(u, p)
            if data.get("status") == "ok" and data.get("user_type") == "supplier":
                self.set_status("Success ✓")
                self.after(150, self._open_main)
            else:
                raise ValueError("Login failed")
        except Exception as e:
            messagebox.showerror("Login failed", str(e))
            self.set_status("")
        finally:
            self.login_btn.config(state="normal")

    def _open_main(self):
        self.withdraw()
        MainWindow(self.api, self).deiconify()


class MainWindow(tk.Toplevel):
    def __init__(self, api: ApiClient, root: tk.Tk):
        super().__init__(root)
        self.api = api
        self.title("Supplier Dashboard")
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        apply_light_style(self)
        accent_bar(self)
        center(self, 1024, 640)

        # Header
        head = ttk.Frame(self, style="Header.TFrame")
        head.pack(fill="x", padx=PADX, pady=(PADY, 8))
        ttk.Label(head, text="Inventory", font=FONT_TITLE).pack(side="left")

        right = ttk.Frame(head, style="Header.TFrame")
        right.pack(side="right")
        ttk.Button(right, text="Orders", style="Primary.TButton",
                   command=lambda: OrdersWindow(self.api, self)).pack(side="left", padx=(0, 8))

        ttk.Button(right, text="Add Item", style="Ghost.TButton",
                   command=lambda: AddItemWindow(self.api, self, on_created=self.load_inventory)
                   ).pack(side="left", padx=(0, 8))

        ttk.Button(right, text="Refresh", style="Ghost.TButton",
                   command=self.load_inventory).pack(side="left")

        # Welcome / hint (optional)
        welcome = card(self)
        ttk.Label(welcome, text="Your inventory", font=FONT_SUB, background=COLORS["card"]).pack(anchor="w")
        ttk.Label(
            welcome,
            text="Search your items below. Use Refresh to sync with server.",
            style="Muted.TLabel", background=COLORS["card"]
        ).pack(anchor="w", pady=(6, 0))

        # Search + tabs
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=PADX, pady=(8, 6))
        ttk.Label(bar, text="Search:").pack(side="right", padx=(8, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        self.search_entry = ttk.Entry(bar, textvariable=self.search_var, width=32)
        self.search_entry.pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=PADX, pady=(0, PADY))
        self.tabs.bind("<<NotebookTabChanged>>", lambda e: self._apply_filter())

        # Build four tables
        self.trees = {}  # key -> (frame, tree, columns)
        self._add_tab(
            key="screws",
            title="Screws",
            preferred_cols=["name", "size", "unit_price", "id"],
            headings={"name": "Name", "size": "Size", "unit_price": "Unit Price", "id": "ID"},
            width_map={"name": 200, "size": 120, "unit_price": 120, "id": 80},
        )
        self._add_tab(
            key="profile_sets",
            title="Profile Sets",
            preferred_cols=["name", "description", "unit_price", "id"],
            headings={"name": "Set Name", "description": "Description", "unit_price": "Unit Price", "id": "ID"},
            width_map={"name": 180, "description": 320, "unit_price": 120, "id": 80},
        )
        self._add_tab(
            key="metal_profiles",
            title="Metal Profiles",
            preferred_cols=["profile_type", "thickness", "price_per_meter", "id"],
            headings={"profile_type": "Type", "thickness": "Thickness", "price_per_meter": "Price/m", "id": "ID"},
            width_map={"profile_type": 180, "thickness": 140, "price_per_meter": 120, "id": 80},
        )
        self._add_tab(
            key="drywall_boards",
            title="Drywall Boards",
            preferred_cols=["color", "size", "price_per_board", "id"],
            headings={"color": "Color", "size": "Size", "price_per_board": "Price/Board", "id": "ID"},
            width_map={"color": 160, "size": 160, "price_per_board": 140, "id": 80},
        )

        # Data store
        self._inventory_raw = {
            "screws": [],
            "profile_sets": [],
            "metal_profiles": [],
            "drywall_boards": [],
        }

        # initial load
        self.load_inventory()

    # --- UI builders ---

    def _add_tab(self, key, title, preferred_cols, headings, width_map):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text=title)

        # Tree
        tree = ttk.Treeview(frame, show="headings", height=14)
        tree.pack(fill="both", expand=True, padx=PADX, pady=PADY)

        # keep config for this tab
        self.trees[key] = {
            "frame": frame,
            "tree": tree,
            "preferred_cols": preferred_cols,
            "headings": headings,
            "width_map": width_map,
            "columns": preferred_cols[:],  # will finalize after first data fetch
        }

    def _configure_tree_columns(self, key, items):
        """Choose columns: prefer preferred_cols; if missing, auto-extend with any other keys present."""
        conf = self.trees[key]
        preferred = conf["preferred_cols"]
        # Collect all keys seen
        all_keys = set()
        for obj in items:
            all_keys.update(obj.keys())
        cols = [c for c in preferred if c in all_keys]
        # append any missing but available keys (deterministic)
        for extra in sorted(all_keys):
            if extra not in cols:
                cols.append(extra)

        conf["columns"] = cols

        tree = conf["tree"]
        tree["columns"] = cols
        for col in cols:
            text = conf["headings"].get(col, col.replace("_", " ").title())
            width = conf["width_map"].get(col, 140)
            tree.heading(col, text=text, anchor="w")
            tree.column(col, anchor="w", width=width, stretch=True)

    # --- Data loading & binding ---

    def load_inventory(self):
        try:
            # expected: {"status":"ok","inventory":{...}}
            resp = self.api.get_supplier_inventory()
            if not resp or resp.get("status") != "ok":
                raise RuntimeError("Bad response")
            inv = resp.get("inventory", {}) or {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory:\n{e}")
            return

        # keep raw (for filtering)
        for key in self._inventory_raw.keys():
            self._inventory_raw[key] = inv.get(key, []) or []

        # configure + populate each tab
        for key, conf in self.trees.items():
            items = self._inventory_raw.get(key, [])
            self._configure_tree_columns(key, items)
            self._populate_tree(key, items)

        # apply current filter (if user already typed)
        self._apply_filter()

    def _populate_tree(self, key, items):
        conf = self.trees[key]
        tree = conf["tree"]
        cols = conf["columns"]

        # clear
        for iid in tree.get_children():
            tree.delete(iid)

        # insert rows
        for obj in items:
            # map any None to "" and numbers to str
            row = []
            for c in cols:
                v = obj.get(c, "")
                if v is None:
                    v = ""
                row.append(str(v))
            tree.insert("", "end", values=row)

    # --- Search filter ---

    def _apply_filter(self):
        query = (self.search_var.get() or "").strip().lower()
        # which tab is active?
        idx = self.tabs.index(self.tabs.select())
        key = list(self.trees.keys())[idx]  # order of creation
        items = self._inventory_raw.get(key, [])
        if not query:
            filtered = items
        else:
            filtered = []
            for obj in items:
                haystack = " ".join(str(v).lower() for v in obj.values() if v is not None)
                if query in haystack:
                    filtered.append(obj)
        self._populate_tree(key, filtered)



class OrdersWindow(tk.Toplevel):
    STATUSES = ["pending", "approved", "completed", "cancelled"]

    def __init__(self, api: ApiClient, parent):
        super().__init__(parent)
        self.api = api
        self.title("Supplier — Orders")
        apply_light_style(self)
        accent_bar(self)
        center(self, 1120, 680)

        # Header
        head = ttk.Frame(self, style="Header.TFrame")
        head.pack(fill="x", padx=PADX, pady=(14, 8))
        ttk.Label(head, text="Orders", font=FONT_TITLE).pack(side="left")
        ttk.Button(head, text="Refresh", style="Ghost.TButton", command=self.load_orders).pack(side="right")

        # Table card
        table_card = card(self, padx=12, pady=12)
        cols = ("id", "order_number", "contractor", "company", "status", "delivery_date", "total_after_tax", "items")
        headers = ["ID", "Order #", "Client", "Company", "Status", "Delivery Date", "Total (after tax)", "Items"]
        widths = [60, 160, 170, 220, 120, 140, 160, 90]
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=16)
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # zebra rows
        self.tree.tag_configure("alt", background=COLORS["row_alt"])

        # Editor
        editor = card(self, padx=12, pady=12)
        ttk.Label(editor, text="Selected Order #", background=COLORS["card"]).grid(row=0, column=0, sticky="w")
        self.sel_lbl = ttk.Label(editor, text="—", style="Muted.TLabel", background=COLORS["card"])
        self.sel_lbl.grid(row=1, column=0, sticky="w", pady=(2, 10))

        ttk.Label(editor, text="Status", background=COLORS["card"]).grid(row=0, column=1, sticky="w")
        self.status_cb = ttk.Combobox(editor, values=self.STATUSES, state="readonly", width=18)
        self.status_cb.grid(row=1, column=1, sticky="w", padx=(10, 16))

        ttk.Label(editor, text="Delivery (YYYY-MM-DD)", background=COLORS["card"]).grid(row=0, column=2, sticky="w")
        self.date_entry = ttk.Entry(editor, width=22)
        self.date_entry.grid(row=1, column=2, sticky="w", padx=(10, 16))

        ttk.Button(editor, text="Save", style="Primary.TButton", command=self.save_changes)\
            .grid(row=1, column=3, padx=(0, 8))
        ttk.Button(editor, text="View Items…", style="Ghost.TButton", command=self.open_details)\
            .grid(row=1, column=4)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self._cache_by_id = {}
        self.selected_id = None
        self.load_orders()

    def load_orders(self):
        try:
            data = self.api.get_orders()
            if data.get("status") != "ok":
                raise ValueError("Failed to load orders.")
            # clear
            for iid in self.tree.get_children():
                self.tree.delete(iid)
            self._cache_by_id.clear()

            for idx, o in enumerate(data["orders"]):
                oid = o["id"]
                self._cache_by_id[oid] = o
                tag = ("alt",) if idx % 2 else ()
                self.tree.insert("", "end", values=(
                    oid,
                    o.get("order_number") or f"ORD-{oid}",
                    o.get("contractor") or "",
                    o.get("company") or "",
                    o.get("status") or "",
                    (o.get("delivery_date") or "")[:10],
                    f"{o.get('total_after_tax', 0):.2f}",
                    "Open"
                ), tags=tag)
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch orders:\n{e}")

    def on_select(self, _evt):
        cur = self.tree.focus()
        if not cur:
            return
        vals = self.tree.item(cur)["values"]
        self.selected_id = int(vals[0])
        self.sel_lbl.config(text=vals[1])
        # preload fields
        current_status = vals[4]
        self.status_cb.set(current_status if current_status in self.STATUSES else self.STATUSES[0])
        self.date_entry.delete(0, tk.END)
        if vals[5]:
            self.date_entry.insert(0, vals[5])

    def save_changes(self):
        if not self.selected_id:
            messagebox.showinfo("No selection", "Select an order first.")
            return
        status = self.status_cb.get().strip()
        date_str = self.date_entry.get().strip()
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid date", "Use YYYY-MM-DD.")
                return

        try:
            self.api.update_order(self.selected_id, status or None, date_str or None)
            messagebox.showinfo("Saved", "Order updated.")
            self.load_orders()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update order:\n{e}")

    def open_details(self):
        if not self.selected_id:
            messagebox.showinfo("No selection", "Select an order first.")
            return
        o = self._cache_by_id.get(self.selected_id)
        if not o:
            messagebox.showerror("Error", "Order not found in memory.")
            return
        OrderDetailsDialog(self, o)


class OrderDetailsDialog(tk.Toplevel):
    def __init__(self, parent, order_dict: dict):
        super().__init__(parent)
        title = order_dict.get("order_number") or f"ORD-{order_dict.get('id')}"
        self.title(f"Order Details — {title}")
        apply_light_style(self)
        accent_bar(self)
        center(self, 860, 560)
        self.transient(parent)
        self.grab_set()

        # Header
        head = ttk.Frame(self, style="Header.TFrame")
        head.pack(fill="x", padx=PADX, pady=(14, 6))
        ttk.Label(head, text=title, font=("Segoe UI Semibold", 16)).pack(anchor="w")
        sub = f"Client: {order_dict.get('contractor') or '-'}   •   Company: {order_dict.get('company') or '-'}"
        ttk.Label(head, text=sub, style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        # Items card
        tbl = card(self, padx=12, pady=12)
        cols = ("name", "unit_price", "qty", "line_total")
        tv = ttk.Treeview(tbl, columns=cols, show="headings", height=12)
        headers = ["Item", "Unit Price", "Qty", "Line Total"]
        widths = [320, 140, 80, 160]
        for c, h, w in zip(cols, headers, widths):
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor="w")
        tv.pack(fill="both", expand=True)
        tv.tag_configure("alt", background=COLORS["row_alt"])

        for idx, it in enumerate(order_dict.get("items", [])):
            tag = ("alt",) if idx % 2 else ()
            tv.insert("", "end", values=(
                it.get("item_name", ""),
                f"{it.get('unit_price', 0):.2f}",
                it.get("quantity", 0),
                f"{it.get('total_price', 0):.2f}"
            ), tags=tag)

        # Totals card
        totals = card(self, padx=12, pady=12)
        b = float(order_dict.get("total_before_tax", 0))
        a = float(order_dict.get("total_after_tax", 0))
        ttk.Label(totals, text=f"Total before tax: {b:.2f}", background=COLORS["card"]).pack(anchor="e")
        ttk.Label(totals, text=f"Total after tax:  {a:.2f}", background=COLORS["card"]).pack(anchor="e")

        # Close
        actions = ttk.Frame(self, style="Header.TFrame")
        actions.pack(fill="x", padx=PADX, pady=(0, 16))
        ttk.Button(actions, text="Close", style="Ghost.TButton", command=self.destroy).pack(side="right")


class AddItemWindow(tk.Toplevel):
    """
    A small modal window to add an inventory item.
    Usage:
        AddItemWindow(api, parent_window, on_created=callback)
    """

    # fixed options per item type & field
    CHOICES_BY_TYPE = {
        "Screw": {
            "screw_type": [
                ("drywall", "Drywall"),
                ("dowel", "Dowel"),
                ("screw", "Regular Screw"),
                ("stainless", "Stainless Steel"),
            ],
            "length_cm": [
                (2.5, "2.5 cm"), (3.5, "3.5 cm"), (4.5, "4.5 cm"),
                (5.0, "5 cm"), (7.0, "7 cm"), (10.0, "10 cm"),
            ],
            "count_per_box": [
                (100, "100"), (500, "500"), (1000, "1000"), (10000, "10000"),
            ],
        },
        "Profile Set": {
            "kind": [
                ("frame", "Frame"),
                ("sash", "Sash"),
            ],
            # tip: aluminum_profile_id stays a free integer (unless you want to load actual rows)
        },
        "Metal Profile": {
            "profile_type": [
                ("stud", "Stud"),
                ("track", "Track"),
            ],
            "size": [
                ("37", "37 mm"), ("50", "50 mm"),
                ("70", "70 mm"), ("100", "100 mm"), ("f47", "F47"),
            ],
        },
        "Drywall Board": {
            "color": [
                ("pink", "Pink"), ("green", "Green"),
                ("white", "White"), ("blue", "Blue"),
            ],
            "size": [
                ("200x120", "200 x 120"),
                ("260x120", "260 x 120"),
                ("300x120", "300 x 120"),
            ],
        },
    }

    def __init__(self, api, parent, on_created=None):
        super().__init__(parent)
        self.api = api
        self.on_created = on_created
        self.title("Add Inventory Item")
        self.transient(parent)
        self.grab_set()
        try:
            # If you have helpers in your app; otherwise harmless to omit
            apply_light_style(self)       # optional
            accent_bar(self)              # optional
            center(self, 520, 360)        # optional
        except Exception:
            self.geometry("520x360")

        PADX = 12
        PADY = 10

        # --- Type selector ---
        header = ttk.Frame(self)
        header.pack(fill="x", padx=PADX, pady=(PADY, 6))
        ttk.Label(header, text="Item Type:").pack(side="left")
        self.item_type = tk.StringVar(value="Screw")
        type_cb = ttk.Combobox(header, textvariable=self.item_type, state="readonly",
                               values=["Screw", "Profile Set", "Metal Profile", "Drywall Board"], width=20)
        type_cb.pack(side="left", padx=(8, 0))
        type_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_form())

        # --- Form area ---
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill="both", expand=True, padx=PADX, pady=(4, PADY))

        # --- Footer buttons ---
        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=PADX, pady=(0, PADY))
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(footer, text="Add", style="Primary.TButton", command=self._submit).pack(side="right", padx=(0, 8))

        # Build initial form
        self._rebuild_form()

    # ---- Form definitions (per type) ----
    def _fields_for_type(self, t):
        """
        Returns a list of (key, label, kind) where kind in {"text","money","int","number"}
        """
        if t == "Screw":
            return [
                ("screw_type", "Type (drywall/dowel/screw/stainless)", "text"),
                ("length_cm", "Length (cm) [2.5,3.5,4.5,5,7,10]", "number"),
                ("count_per_box", "Count per Box [100,500,1000,10000]", "int"),
                ("price_per_100", "Price per 100", "money"),
            ]
        if t == "Profile Set":
            return [
                ("aluminum_profile_id", "AluminumProfile ID", "int"),
                ("kind", "Kind (frame/sash)", "text"),
                ("name", "Name", "text"),
                ("code_string", "Code String", "text"),
                ("set_code", "Set Code (unique)", "int"),
                ("weight_per_meter", "Weight per Meter (kg/m)", "money"),
                ("price_per_kilo", "Price per Kilo", "money"),
            ]
        if t == "Metal Profile":
            return [
                ("profile_type", "Type (stud/track)", "text"),
                ("size", "Size (37/50/70/100/f47)", "text"),
                ("length_meters", "Length (m)", "number"),
                ("quantity", "Quantity", "int"),
                ("price_per_piece", "Price per Piece", "money"),
            ]
        if t == "Drywall Board":
            return [
                ("color", "Color (pink/green/white/blue)", "text"),
                ("size", "Size (200x120/260x120/300x120)", "text"),
                ("thickness_mm", "Thickness (mm)", "int"),
                ("quantity", "Quantity", "int"),
                ("price_per_board", "Price per Board", "money"),
            ]
        return []

    def _rebuild_form(self):
        for w in self.form_frame.winfo_children():
            w.destroy()

        self.inputs = {}  # key -> (widget, kind[, choice_map])

        t = self.item_type.get()
        rows = self._fields_for_type(t)
        choices_for_type = self.CHOICES_BY_TYPE.get(t, {})

        for key, label, kind in rows:
            r = ttk.Frame(self.form_frame)
            r.pack(fill="x", pady=6)

            ttk.Label(r, text=label, width=22).pack(side="right")

            # If this field has fixed choices -> use Combobox
            if key in choices_for_type:
                options = choices_for_type[key]  # list of (value, label)
                labels = [lab for _, lab in options]
                value_by_label = {lab: val for val, lab in options}

                cb = ttk.Combobox(r, state="readonly", values=labels)
                cb.pack(side="right", fill="x", expand=True)
                # store the mapping so _submit can convert label -> real value
                self.inputs[key] = (cb, kind, value_by_label)
            else:
                ent = ttk.Entry(r)
                ent.pack(side="right", fill="x", expand=True)
                self.inputs[key] = (ent, kind)

    # ---- Submission ----
    def _submit(self):
        t = self.item_type.get()
        payload = {}

        for key, meta in self.inputs.items():
            # meta can be (widget, kind) or (widget, kind, choice_map)
            widget, kind = meta[0], meta[1]
            choice_map = meta[2] if len(meta) > 2 else None

            if isinstance(widget, ttk.Combobox) and choice_map:
                label = widget.get().strip()
                if not label:
                    messagebox.showerror("Missing", f"Please select {key.replace('_', ' ')}")
                    widget.focus_set();
                    return
                val = choice_map[label]  # already correct type (str/int/float)
            else:
                val = widget.get().strip()
                if not val:
                    messagebox.showerror("Missing", f"Please enter {key.replace('_', ' ')}")
                    widget.focus_set();
                    return
                if kind in ("money", "number"):
                    try:
                        val = float(val.replace(",", "."))
                    except ValueError:
                        messagebox.showerror("Invalid number", f"{key.replace('_', ' ').title()} must be a number")
                        widget.focus_set();
                        return
                elif kind == "int":
                    try:
                        val = int(val)
                    except ValueError:
                        messagebox.showerror("Invalid integer", f"{key.replace('_', ' ').title()} must be an integer")
                        widget.focus_set();
                        return

            payload[key] = val

        try:
            if t == "Screw":
                resp = self.api.add_screw(
                    screw_type=payload["screw_type"],
                    length_cm=payload["length_cm"],
                    count_per_box=payload["count_per_box"],
                    price_per_100=payload["price_per_100"],
                )
            elif t == "Profile Set":
                resp = self.api.add_profile_set(
                    aluminum_profile_id=payload["aluminum_profile_id"],
                    kind=payload["kind"],
                    name=payload["name"],
                    code_string=payload["code_string"],
                    set_code=payload["set_code"],
                    weight_per_meter=payload["weight_per_meter"],
                    price_per_kilo=payload["price_per_kilo"],
                )
            elif t == "Metal Profile":
                resp = self.api.add_metal_profile(
                    profile_type=payload["profile_type"],
                    size=payload["size"],
                    length_meters=payload["length_meters"],
                    quantity=payload["quantity"],
                    price_per_piece=payload["price_per_piece"],
                )
            elif t == "Drywall Board":
                resp = self.api.add_drywall_board(
                    color=payload["color"],
                    size=payload["size"],
                    thickness_mm=payload["thickness_mm"],
                    quantity=payload["quantity"],
                    price_per_board=payload["price_per_board"],
                )
            else:
                messagebox.showerror("Error", "Unknown item type");
                return
        except Exception as e:
            messagebox.showerror("Error", f"Request failed:\n{e}");
            return

        if not resp or resp.get("status") != "ok":
            messagebox.showerror("Error", f"{resp.get('message') or resp.get('errors') or 'Unknown error'}");
            return

        messagebox.showinfo("Success", "Item added.")
        if callable(self.on_created):
            try:
                self.on_created()
            except Exception:
                pass
        self.destroy()


# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        import requests  # ensure installed
    except ImportError:
        print("Please install dependencies first: pip install requests")
    app = LoginWindow()
    app.mainloop()
