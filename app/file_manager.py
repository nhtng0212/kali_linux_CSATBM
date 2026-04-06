import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import threading
import shutil

DEVICE_PATH = "/dev/cipher_dev"
CHUNK_SIZE = 4096
PREVIEW_SIZE = 1024

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

class CipherShiftPro:
    def __init__(self, root):
        self.root = root
        self.root.title("CipherShift - Secure Kernel File Manager")
        self.root.geometry("1000x650") # Mở rộng giao diện thêm một chút
        self.root.configure(bg="#FFFFFF")

        self.state = {
            'encrypt': {'mode': None, 'path': None, 'files': [], 'temp_files': [], 'total_size': 0, 'is_processed': False},
            'decrypt': {'mode': None, 'path': None, 'files': [], 'temp_files': [], 'total_size': 0, 'is_processed': False}
        }
        self.widgets = {'encrypt': {}, 'decrypt': {}}

        self.setup_ui()

    def setup_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg="#FFFFFF")
        header.pack(fill=tk.X, padx=20, pady=10)

        lbl_title = tk.Label(header, text="HỆ THỐNG BẢO MẬT DỮ LIỆU CẤP KERNEL", 
                             font=("Segoe UI", 18, "bold"), bg="#FFFFFF", fg="#2C3E50")
        lbl_title.pack(side=tk.LEFT)

        lbl_dev = tk.Label(header, text=f"Driver: {DEVICE_PATH}", 
                           font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#27AE60")
        lbl_dev.pack(side=tk.RIGHT)

        # --- TABS STYLE ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#FFFFFF")
        style.configure("TNotebook.Tab", background="#F2F3F4", font=("Segoe UI", 11, "bold"), padding=[15, 8])
        style.map("TNotebook.Tab", 
                  background=[("selected", "#3498DB")], 
                  foreground=[("selected", "#FFFFFF")],
                  padding=[("selected", [25, 12])], 
                  expand=[("selected", [1, 1, 1, 0])])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tab_enc = tk.Frame(notebook, bg="#FFFFFF")
        tab_dec = tk.Frame(notebook, bg="#FFFFFF")

        notebook.add(tab_enc, text="  🔒 Bảo mật (Mã hóa)  ")
        notebook.add(tab_dec, text="  🔓 Khôi phục (Giải mã)  ")

        self.build_tab(tab_enc, 'encrypt')
        self.build_tab(tab_dec, 'decrypt')

    def build_tab(self, parent, op_type):
        left_frame = tk.Frame(parent, bg="#FFFFFF", width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_frame.pack_propagate(False)

        right_frame = tk.Frame(parent, bg="#F9F9F9", bd=1, relief=tk.SOLID)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ==========================================
        # LEFT FRAME: CONTROL PANEL
        # ==========================================
        mode_text = "🔒 MÃ HÓA BẢO MẬT" if op_type == 'encrypt' else "🔓 GIẢI MÃ KHÔI PHỤC"
        mode_color = "#E74C3C" if op_type == 'encrypt' else "#8E44AD"
        tk.Label(left_frame, text=mode_text, font=("Segoe UI", 14, "bold"), fg=mode_color, bg="#FFFFFF", anchor="w").pack(fill=tk.X, pady=(0, 10))

        drop_zone = tk.Label(left_frame, text="📥 KÉO THẢ FILE / FOLDER VÀO ĐÂY", 
                             font=("Segoe UI", 11, "bold"), bg="#FBFCFC", fg="#7F8C8D", 
                             relief=tk.GROOVE, bd=2, height=4)
        drop_zone.pack(fill=tk.X, pady=(0, 10))

        btn_frame = tk.Frame(left_frame, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        btn_sel_file = tk.Button(btn_frame, text="📄 Chọn File", font=("Segoe UI", 10, "bold"), bg="#ECF0F1", fg="#2C3E50", relief=tk.FLAT, cursor="hand2", command=lambda: self.select_file(op_type))
        btn_sel_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_sel_folder = tk.Button(btn_frame, text="📁 Chọn Folder", font=("Segoe UI", 10, "bold"), bg="#ECF0F1", fg="#2C3E50", relief=tk.FLAT, cursor="hand2", command=lambda: self.select_folder(op_type))
        btn_sel_folder.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        drop_zone.drop_target_register(DND_FILES)
        drop_zone.dnd_bind('<<Drop>>', lambda e, op=op_type: self.handle_drop(e, op))
        left_frame.drop_target_register(DND_FILES)
        left_frame.dnd_bind('<<Drop>>', lambda e, op=op_type: self.handle_drop(e, op))

        lbl_name = tk.Label(left_frame, text="Mục tiêu: Chưa chọn", bg="#FFFFFF", fg="#34495E", font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_name.pack(fill=tk.X)

        lbl_size = tk.Label(left_frame, text="Tổng dung lượng: N/A", bg="#FFFFFF", fg="#34495E", font=("Segoe UI", 10), anchor="w")
        lbl_size.pack(fill=tk.X)

        tk.Label(left_frame, text="", bg="#FFFFFF").pack(pady=5)

        progress = ttk.Progressbar(left_frame, orient="horizontal", mode="determinate")

        text_act = "MÃ HÓA NGAY" if op_type == 'encrypt' else "GIẢI MÃ NGAY"
        btn_action = tk.Button(left_frame, text=text_act, font=("Segoe UI", 12, "bold"),
                               bg="#2ECC71", fg="white", relief=tk.FLAT, height=2, state=tk.DISABLED, cursor="hand2",
                               command=lambda: self.process_start(op_type))
        btn_action.pack(fill=tk.X, pady=10)

        btn_export = tk.Button(left_frame, text="💾 XUẤT KẾT QUẢ", font=("Segoe UI", 12, "bold"),
                               bg="#3498DB", fg="white", relief=tk.FLAT, height=2, state=tk.DISABLED, cursor="hand2",
                               command=lambda: self.export_data(op_type))
        btn_export.pack(fill=tk.X)

        # ==========================================
        # RIGHT FRAME: PANED WINDOW (LIST + PREVIEW)
        # ==========================================
        paned = tk.PanedWindow(right_frame, orient=tk.VERTICAL, bg="#BDC3C7", sashwidth=4, sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)

        # KHUNG 1: DANH SÁCH FILE (TOP)
        list_container = tk.Frame(paned, bg="#F9F9F9")
        tk.Label(list_container, text="📑 DANH SÁCH FILE (Click để xem nội dung)", font=("Segoe UI", 10, "bold"), bg="#F9F9F9", fg="#2C3E50", anchor="w").pack(fill=tk.X, padx=5, pady=5)
        
        listbox_frame = tk.Frame(list_container)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        scroll_y = tk.Scrollbar(listbox_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = tk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        listbox = tk.Listbox(listbox_frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, font=("Consolas", 10), selectbackground="#3498DB", selectforeground="white", activestyle="none")
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_y.config(command=listbox.yview)
        scroll_x.config(command=listbox.xview)

        # Đăng ký sự kiện Click vào Listbox
        listbox.bind('<<ListboxSelect>>', lambda e, op=op_type: self.on_listbox_select(e, op))

        paned.add(list_container, minsize=120)

        # KHUNG 2: NỘI DUNG PREVIEW (BOTTOM)
        prev_container = tk.Frame(paned, bg="#F9F9F9")
        tk.Label(prev_container, text="👁️ XEM TRƯỚC NỘI DUNG (1KB đầu tiên)", font=("Segoe UI", 10, "bold"), bg="#F9F9F9", fg="#2C3E50", anchor="w").pack(fill=tk.X, padx=5, pady=5)

        text_frame = tk.Frame(prev_container)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        txt_scroll = tk.Scrollbar(text_frame)
        txt_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        txt_preview = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#FFFFFF", fg="#2C3E50", bd=1, relief=tk.SOLID, yscrollcommand=txt_scroll.set)
        txt_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt_scroll.config(command=txt_preview.yview)

        txt_preview.insert(tk.END, "Vui lòng chọn một file từ danh sách bên trên để hiển thị nội dung...")
        txt_preview.config(state=tk.DISABLED)

        paned.add(prev_container, minsize=200)

        # Cho phép kéo thả vào cả 2 khung bên phải
        listbox.drop_target_register(DND_FILES)
        listbox.dnd_bind('<<Drop>>', lambda e, op=op_type: self.handle_drop(e, op))
        txt_preview.drop_target_register(DND_FILES)
        txt_preview.dnd_bind('<<Drop>>', lambda e, op=op_type: self.handle_drop(e, op))

        self.widgets[op_type] = {
            'drop_zone': drop_zone, 'btn_sel_file': btn_sel_file, 'btn_sel_folder': btn_sel_folder,
            'lbl_name': lbl_name, 'lbl_size': lbl_size, 'progress': progress, 
            'btn_action': btn_action, 'btn_export': btn_export, 
            'listbox': listbox, 'txt_preview': txt_preview
        }

    # --- LOGIC XỬ LÝ ĐẦU VÀO ---
    def select_file(self, op_type):
        path = filedialog.askopenfilename(title="Chọn file xử lý")
        if path: self.load_target(path, op_type, is_file=True)

    def select_folder(self, op_type):
        path = filedialog.askdirectory(title="Chọn thư mục xử lý")
        if path: self.load_target(path, op_type, is_file=False)

    def handle_drop(self, event, op_type):
        files = self.root.tk.splitlist(event.data)
        if files:
            path = files[0]
            self.load_target(path, op_type, is_file=os.path.isfile(path))

    def load_target(self, path, op_type, is_file):
        state = self.state[op_type]
        w = self.widgets[op_type]
        
        state['path'] = path
        state['mode'] = 'file' if is_file else 'folder'
        state['temp_files'] = []
        state['is_processed'] = False # Đặt lại trạng thái chưa xử lý

        w['listbox'].delete(0, tk.END)

        if is_file:
            state['files'] = [path]
            state['total_size'] = os.path.getsize(path)
            w['lbl_name'].config(text=f"File: {os.path.basename(path)}")
            w['listbox'].insert(tk.END, os.path.basename(path))
        else:
            file_list = []
            total_sz = 0
            for root_dir, _, filenames in os.walk(path):
                for fname in filenames:
                    fpath = os.path.join(root_dir, fname)
                    file_list.append(fpath)
                    total_sz += os.path.getsize(fpath)
            
            if not file_list:
                messagebox.showerror("Lỗi", "Thư mục trống, không có file để xử lý!")
                return

            state['files'] = file_list
            state['total_size'] = total_sz
            w['lbl_name'].config(text=f"Folder: {os.path.basename(path)} ({len(file_list)} files)")
            
            for f in file_list:
                rel_path = os.path.relpath(f, path)
                sz = format_size(os.path.getsize(f))
                w['listbox'].insert(tk.END, f"{rel_path} ({sz})")

        w['lbl_size'].config(text=f"Tổng dung lượng: {format_size(state['total_size'])}")
        w['btn_action'].config(state=tk.NORMAL)
        w['btn_export'].config(state=tk.DISABLED)
        w['progress'].pack_forget()

        # Tự động click (chọn) dòng đầu tiên trong Listbox
        if state['files']:
            w['listbox'].selection_set(0)
            self.on_listbox_select(None, op_type)

    # --- SỰ KIỆN CLICK VÀO LISTBOX ---
    def on_listbox_select(self, event, op_type):
        state = self.state[op_type]
        w = self.widgets[op_type]
        
        selection = w['listbox'].curselection()
        if not selection:
            return
            
        index = selection[0]
        
        # Kiểm tra xem đang ở trạng thái nào để nạp file tương ứng
        if state['is_processed']:
            target_path = state['temp_files'][index]
            prefix = "DỮ LIỆU ĐÃ QUA KERNEL"
        else:
            target_path = state['files'][index]
            prefix = "DỮ LIỆU GỐC"
            
        self.load_preview_file(target_path, w['txt_preview'], prefix)

    # --- ĐỌC NỘI DUNG PREVIEW THỰC TẾ ---
    def load_preview_file(self, path, widget, prefix_type):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        try:
            with open(path, 'rb') as f:
                data = f.read(PREVIEW_SIZE)
            
            file_name = os.path.basename(path).replace(".tmp_kernel", "")
            header = f"--- [{prefix_type}] - {file_name} ---\n\n"
            
            try:
                # Cố gắng dịch file dưới dạng Text
                widget.insert(tk.END, header + data.decode('utf-8'))
            except UnicodeDecodeError:
                # Nếu là file nhị phân/đã mã hóa, in ra mã HEX
                widget.insert(tk.END, header + "[File Binary / Dữ liệu đã mã hóa]\nHEX VIEW:\n" + data.hex(' ', 2))
        except Exception as e:
            widget.insert(tk.END, f"Không thể đọc file: {e}")
        widget.config(state=tk.DISABLED)

    # --- KERNEL PROCESSING ---
    def process_start(self, op_type):
        w = self.widgets[op_type]
        w['btn_action'].config(state=tk.DISABLED)
        w['btn_sel_file'].config(state=tk.DISABLED)
        w['btn_sel_folder'].config(state=tk.DISABLED)
        
        w['progress'].pack(fill=tk.X, before=w['btn_action'], pady=(0, 10))
        w['progress']['value'] = 0

        threading.Thread(target=self.kernel_worker, args=(op_type,), daemon=True).start()

    def kernel_worker(self, op_type):
        state = self.state[op_type]
        files = state['files']
        total_size = state['total_size']
        processed_bytes = 0
        temp_files = []

        try:
            fd_driver = os.open(DEVICE_PATH, os.O_RDWR)

            for fpath in files:
                temp_out = fpath + ".tmp_kernel"
                temp_files.append(temp_out)
                file_size = os.path.getsize(fpath)

                with open(fpath, 'rb') as f_in, open(temp_out, 'wb') as f_out:
                    while True:
                        chunk = f_in.read(CHUNK_SIZE)
                        if not chunk: break

                        read_len = len(chunk)
                        is_padded = False
                        
                        if read_len % 2 != 0:
                            chunk += b'\x00'
                            is_padded = True

                        os.write(fd_driver, chunk)
                        processed_chunk = os.read(fd_driver, len(chunk))

                        if is_padded:
                            processed_chunk = processed_chunk[:-1]

                        f_out.write(processed_chunk)
                        processed_bytes += read_len
                        
                        percent = int((processed_bytes / total_size) * 100) if total_size > 0 else 100
                        self.root.after(0, self.update_progress, op_type, percent)

            os.close(fd_driver)
            state['temp_files'] = temp_files
            self.root.after(0, self.process_success, op_type)

        except Exception as e:
            self.root.after(0, self.process_error, op_type, str(e))

    def update_progress(self, op_type, percent):
        self.widgets[op_type]['progress']['value'] = percent

    def process_success(self, op_type):
        w = self.widgets[op_type]
        state = self.state[op_type]
        
        w['btn_sel_file'].config(state=tk.NORMAL)
        w['btn_sel_folder'].config(state=tk.NORMAL)
        w['btn_export'].config(state=tk.NORMAL)
        
        # Bật cờ đã xử lý để Listbox biết đường load file temp
        state['is_processed'] = True 

        messagebox.showinfo("Hoàn tất", "Xử lý bằng Kernel thành công!\nBạn có thể click vào danh sách file để xem trước kết quả.\nHãy ấn XUẤT KẾT QUẢ để lưu.")
        
        # Tự động cập nhật nội dung của file đang được highlight trong Listbox
        self.on_listbox_select(None, op_type)

    def process_error(self, op_type, err):
        w = self.widgets[op_type]
        w['btn_sel_file'].config(state=tk.NORMAL)
        w['btn_sel_folder'].config(state=tk.NORMAL)
        w['btn_action'].config(state=tk.NORMAL)
        messagebox.showerror("Lỗi Kernel", f"Quá trình thất bại:\n{err}\nĐảm bảo đã chạy 'sudo chmod 666 /dev/cipher_dev'")

    # --- XUẤT DỮ LIỆU ---
    def export_data(self, op_type):
        state = self.state[op_type]
        w = self.widgets[op_type]

        try:
            if state['mode'] == 'file':
                orig_path = state['files'][0]
                sug_name = os.path.basename(orig_path) + ".cipher" if op_type == 'encrypt' else os.path.basename(orig_path).replace(".cipher", "")
                save_path = filedialog.asksaveasfilename(initialfile=sug_name, title="Lưu file kết quả")
                
                if save_path:
                    shutil.move(state['temp_files'][0], save_path)
                    messagebox.showinfo("Thành công", f"Đã lưu file tại:\n{save_path}")
                else: return 
                
            else: 
                out_dir = filedialog.askdirectory(title="Chọn thư mục đích để lưu toàn bộ kết quả")
                if out_dir:
                    for i, temp_path in enumerate(state['temp_files']):
                        orig_path = state['files'][i]
                        rel_path = os.path.relpath(orig_path, state['path'])
                        
                        if op_type == 'encrypt':
                            new_name = rel_path + ".cipher"
                        else:
                            new_name = rel_path.replace(".cipher", "")
                            if new_name == rel_path: new_name += "_decrypted"
                            
                        final_path = os.path.join(out_dir, new_name)
                        os.makedirs(os.path.dirname(final_path), exist_ok=True)
                        shutil.move(temp_path, final_path)
                        
                    messagebox.showinfo("Thành công", f"Đã xuất toàn bộ Folder tại:\n{out_dir}")
                else: return 

            w['btn_export'].config(state=tk.DISABLED)
            w['btn_action'].config(state=tk.DISABLED)
            w['lbl_name'].config(text="Mục tiêu: Chưa chọn")
            w['lbl_size'].config(text="Tổng dung lượng: N/A")
            w['listbox'].delete(0, tk.END)
            w['txt_preview'].config(state=tk.NORMAL)
            w['txt_preview'].delete(1.0, tk.END)
            w['txt_preview'].insert(tk.END, "Vui lòng chọn một file từ danh sách bên trên để hiển thị nội dung...")
            w['txt_preview'].config(state=tk.DISABLED)
            
            state['temp_files'] = []
            state['is_processed'] = False

        except Exception as e:
            messagebox.showerror("Lỗi Lưu Dữ liệu", str(e))

if __name__ == "__main__":
    if not os.path.exists(DEVICE_PATH):
        print(f"[-] LỖI: Không tìm thấy Driver {DEVICE_PATH}")
        print("[-] Vui lòng nạp driver bằng lệnh: sudo insmod driver/cipher_driver.ko")
        import sys; sys.exit(1)

    root = TkinterDnD.Tk()
    app = CipherShiftPro(root)
    root.mainloop()