import customtkinter as ctk
import random
import time
import threading
import bisect
from tkinter import messagebox

# --- Cấu trúc B+ Tree Tối ưu (Dùng Delta Compression) ---
class CompressedNode:
    __slots__ = ['is_leaf', 'keys', 'values', 'children', 'base_key']
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.values = []
        self.children = []
        self.base_key = 0

class CompressedBPlusTree:
    def __init__(self, order=1000):
        self.root = CompressedNode(is_leaf=True)
        self.order = order

    def find(self, key):
        curr = self.root
        while not curr.is_leaf:
            idx = bisect.bisect_right(curr.keys, key - curr.base_key)
            curr = curr.children[idx]
        delta = key - curr.base_key
        idx = bisect.bisect_left(curr.keys, delta)
        if idx < len(curr.keys) and curr.keys[idx] == delta:
            return curr.values[idx]
        return None

    def insert(self, key, info):
        stack = []
        curr = self.root
        while not curr.is_leaf:
            stack.append(curr)
            idx = bisect.bisect_right(curr.keys, key - curr.base_key)
            curr = curr.children[idx]
        if not curr.keys: curr.base_key = key
        delta = key - curr.base_key
        idx = bisect.bisect_left(curr.keys, delta)
        if idx < len(curr.keys) and curr.keys[idx] == delta:
            curr.values[idx] = info
            return
        curr.keys.insert(idx, delta)
        curr.values.insert(idx, info)
        if len(curr.keys) >= self.order: self._split(curr, stack)

    def delete(self, key):
        curr = self.root
        while not curr.is_leaf:
            idx = bisect.bisect_right(curr.keys, key - curr.base_key)
            curr = curr.children[idx]
        delta = key - curr.base_key
        idx = bisect.bisect_left(curr.keys, delta)
        if idx < len(curr.keys) and curr.keys[idx] == delta:
            curr.keys.pop(idx)
            curr.values.pop(idx)
            return True
        return False

    def _split(self, node, stack):
        mid = len(node.keys) // 2
        split_full_key = node.base_key + node.keys[mid]
        new_node = CompressedNode(is_leaf=node.is_leaf)
        new_node.base_key = split_full_key
        if node.is_leaf:
            new_node.keys = [(node.base_key + k) - new_node.base_key for k in node.keys[mid:]]
            new_node.values = node.values[mid:]
            node.keys = node.keys[:mid]
            node.values = node.values[:mid]
            up_key = split_full_key
        else:
            new_node.keys = [(node.base_key + k) - new_node.base_key for k in node.keys[mid+1:]]
            new_node.children = node.children[mid+1:]
            up_key = split_full_key
            node.keys = node.keys[:mid]
            node.children = node.children[:mid+1]
        if not stack:
            new_root = CompressedNode(is_leaf=False)
            new_root.base_key = node.base_key
            new_root.keys = [up_key - new_root.base_key]
            new_root.children = [node, new_node]
            self.root = new_root
        else:
            parent = stack.pop()
            idx = bisect.bisect_right(parent.keys, up_key - parent.base_key)
            parent.keys.insert(idx, up_key - parent.base_key)
            parent.children.insert(idx + 1, new_node)
            if len(parent.keys) >= self.order: self._split(parent, stack)

# --- Giao diện Ứng dụng ---
class BankApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Quản Lý Ngân Hàng - B+ Tree")
        self.geometry("950x600")
        ctk.set_appearance_mode("dark")
        
        self.tree = CompressedBPlusTree(order=1000)
        self.is_loading = True

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR (MENU CHỨC NĂNG)
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="BANK MANAGER", font=("Arial", 20, "bold"))
        self.logo.pack(pady=30)

        self.btn_find = ctk.CTkButton(self.sidebar, text="1. Tìm kiếm chi tiết", command=lambda: self.show_frame("find"), height=40)
        self.btn_find.pack(pady=10, padx=20)

        self.btn_add = ctk.CTkButton(self.sidebar, text="2. Thêm khách hàng mới", command=lambda: self.show_frame("add"), height=40)
        self.btn_add.pack(pady=10, padx=20)

        self.btn_edit = ctk.CTkButton(self.sidebar, text="3. Cập nhật thông tin", command=lambda: self.show_frame("edit"), height=40)
        self.btn_edit.pack(pady=10, padx=20)

        self.btn_del = ctk.CTkButton(self.sidebar, text="4. Xóa tài khoản", command=lambda: self.show_frame("del"), height=40)
        self.btn_del.pack(pady=10, padx=20)

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Đang nạp 5 triệu dân...", text_color="yellow")
        self.lbl_status.pack(side="bottom", pady=20)

        # 2. MAIN AREA
        self.main_container = ctk.CTkFrame(self, corner_radius=15)
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.current_frame = None
        self.show_frame("find") # Mặc định mở tab tìm kiếm

        # Load data ngầm
        threading.Thread(target=self.load_initial_data, daemon=True).start()

    def show_frame(self, mode):
        if self.current_frame: self.current_frame.destroy()
        
        self.current_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_map = {"find": "TÌM KIẾM CHI TIẾT", "add": "THÊM KHÁCH HÀNG", "edit": "CẬP NHẬT SỐ DƯ", "del": "XÓA TÀI KHOẢN"}
        lbl = ctk.CTkLabel(self.current_frame, text=title_map[mode], font=("Arial", 22, "bold"))
        lbl.pack(pady=20)

        self.ent_stk = ctk.CTkEntry(self.current_frame, placeholder_text="Nhập Số tài khoản (STK)", width=350, height=45)
        self.ent_stk.pack(pady=10)

        if mode == "add":
            self.ent_name = ctk.CTkEntry(self.current_frame, placeholder_text="Tên khách hàng", width=350)
            self.ent_name.pack(pady=10)
            self.ent_bal = ctk.CTkEntry(self.current_frame, placeholder_text="Số dư ban đầu", width=350)
            self.ent_bal.pack(pady=10)
            btn = ctk.CTkButton(self.current_frame, text="XÁC NHẬN THÊM", fg_color="green", command=self.do_add)
            btn.pack(pady=20)
        
        elif mode == "edit":
            self.ent_new_bal = ctk.CTkEntry(self.current_frame, placeholder_text="Số dư mới", width=350)
            self.ent_new_bal.pack(pady=10)
            btn = ctk.CTkButton(self.current_frame, text="CẬP NHẬT", fg_color="orange", command=self.do_edit)
            btn.pack(pady=20)

        elif mode == "find":
            btn = ctk.CTkButton(self.current_frame, text="TRUY VẤN", command=self.do_find)
            btn.pack(pady=10)
            self.txt_res = ctk.CTkTextbox(self.current_frame, width=500, height=200)
            self.txt_res.pack(pady=20)

        elif mode == "del":
            btn = ctk.CTkButton(self.current_frame, text="XÓA VĨNH VIỄN", fg_color="red", command=self.do_del)
            btn.pack(pady=20)

    # --- LOGIC XỬ LÝ ---
    def load_initial_data(self):
        for i in range(1, 5000001):
            self.tree.insert(i, {"name": f"Khách hàng {i}", "bal": random.randint(1000, 100000000)})
        self.is_loading = False
        self.lbl_status.configure(text="● Hệ thống Sẵn sàng", text_color="green")

    def do_find(self):
        stk = int(self.ent_stk.get())
        t1 = time.perf_counter()
        res = self.tree.find(stk)
        t2 = (time.perf_counter() - t1) * 1000
        self.txt_res.delete("0.0", "end")
        if res:
            self.txt_res.insert("end", f"TÊN: {res['name']}\nSỐ DƯ: {res['bal']:,} VNĐ\nTHỜI GIAN: {t2:.4f} ms")
        else: messagebox.showinfo("Kết quả", "Không tìm thấy!")

    def do_add(self):
        stk = int(self.ent_stk.get())
        self.tree.insert(stk, {"name": self.ent_name.get(), "bal": int(self.ent_bal.get())})
        messagebox.showinfo("Thành công", f"Đã thêm STK {stk}")

    def do_edit(self):
        stk = int(self.ent_stk.get())
        res = self.tree.find(stk)
        if res:
            res['bal'] = int(self.ent_new_bal.get())
            messagebox.showinfo("Thành công", "Đã cập nhật số dư.")
        else: messagebox.showerror("Lỗi", "Không tìm thấy STK.")

    def do_del(self):
        stk = int(self.ent_stk.get())
        if self.tree.delete(stk): messagebox.showinfo("Xóa", f"Đã xóa tài khoản {stk}")
        else: messagebox.showerror("Lỗi", "Không tìm thấy STK.")

if __name__ == "__main__":
    app = BankApp()
    app.mainloop()