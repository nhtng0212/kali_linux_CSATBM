import tkinter as tk
import os
import struct
import threading
import time

DEVICE_PATH = "/dev/usb_mouse_dev"

class MouseRadarUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Radar - Academy of Cryptography Techniques")
        self.root.geometry("1150x650")
        self.root.configure(bg="#F4F6F7")

        # Tọa độ ảo trên Radar
        self.virtual_x, self.virtual_y = 250, 200
        self.running = True
        
        # Bộ đếm giữ đèn sáng cho nút bấm và con lăn
        self.wheel_timer = 0
        self.wheel_val = 0
        
        self.setup_ui()
        threading.Thread(target=self.update_loop, daemon=True).start()

    def setup_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg="#2C3E50", height=80)
        header.pack(fill=tk.X)
        tk.Label(header, text="KERNEL MOUSE MONITOR", 
                 font=("Segoe UI", 22, "bold"), fg="#ECF0F1", bg="#2C3E50").pack(pady=20)

        # --- STATUS BAR ---
        self.lbl_status = tk.Label(self.root, text="SCANNING FOR KERNEL MODULE...", 
                                   font=("Segoe UI", 11, "bold"), bg="#EBEDEF", fg="#7F8C8D")
        self.lbl_status.pack(fill=tk.X, padx=20, pady=10)

        main_container = tk.Frame(self.root, bg="#F4F6F7")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # --- CỘT 1: THIẾT BỊ VẬT LÝ & THÔNG SỐ (BÊN TRÁI) ---
        left_col = tk.Frame(main_container, bg="#F4F6F7")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 1. Hình vẽ con chuột
        mouse_frame = tk.LabelFrame(left_col, text=" PHYSICAL DEVICE ", font=("Segoe UI", 10, "bold"), bg="white")
        mouse_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.canvas_mouse = tk.Canvas(mouse_frame, width=220, height=280, bg="white", highlightthickness=0)
        self.canvas_mouse.pack(pady=10)
        
        # Thân chuột
        self.canvas_mouse.create_oval(40, 40, 180, 240, fill="#F2F4F4", outline="#BDC3C7", width=3)
        # Nút Trái/Phải
        self.btn_l = self.canvas_mouse.create_arc(40, 40, 180, 240, start=90, extent=90, fill="#E5E8E8", outline="#BDC3C7", width=2, style=tk.PIESLICE)
        self.btn_r = self.canvas_mouse.create_arc(40, 40, 180, 240, start=0, extent=90, fill="#E5E8E8", outline="#BDC3C7", width=2, style=tk.PIESLICE)
        # Con lăn và Mũi tên ▲/▼
        self.wheel_obj = self.canvas_mouse.create_oval(95, 75, 125, 120, fill="#95A5A6", outline="#7F8C8D", width=2)
        self.arr_up = self.canvas_mouse.create_text(110, 60, text="▲", font=("Arial", 18, "bold"), fill="#F2F4F4")
        self.arr_down = self.canvas_mouse.create_text(110, 135, text="▼", font=("Arial", 18, "bold"), fill="#F2F4F4")

        # 2. Thông số dữ liệu (RAW & COORDS)
        data_frame = tk.LabelFrame(left_col, text=" DATA STREAM ", font=("Segoe UI", 10, "bold"), bg="white")
        data_frame.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_coords = tk.Label(data_frame, text="COORD: X=0, Y=0", font=("Consolas", 14, "bold"), fg="#E74C3C", bg="white")
        self.lbl_coords.pack(pady=5)
        
        self.lbl_raw = tk.Label(data_frame, text="RAW: 00 00 00 00 00", font=("Consolas", 12, "bold"), fg="#3498DB", bg="white")
        self.lbl_raw.pack(pady=5)

        # 3. Trạng thái hướng (DIRECTION)
        dir_frame = tk.LabelFrame(left_col, text=" MOVEMENT ANALYTICS ", font=("Segoe UI", 10, "bold"), bg="white")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lbl_dir_x = tk.Label(dir_frame, text="H-MOVE: IDLE", font=("Segoe UI", 11, "bold"), bg="white", fg="#7F8C8D")
        self.lbl_dir_x.pack()
        self.lbl_dir_y = tk.Label(dir_frame, text="V-MOVE: IDLE", font=("Segoe UI", 11, "bold"), bg="white", fg="#7F8C8D")
        self.lbl_dir_y.pack()

        # --- CỘT 2: VIRTUAL RADAR (BÊN PHẢI) ---
        radar_frame = tk.LabelFrame(main_container, text=" KERNEL RADAR SPACE ", font=("Segoe UI", 10, "bold"), bg="white")
        radar_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.canvas_radar = tk.Canvas(radar_frame, width=500, height=400, bg="#1B2631", highlightthickness=0)
        self.canvas_radar.pack(padx=20, pady=20)
        
        # Lưới Radar
        for i in range(0, 500, 50): self.canvas_radar.create_line(i, 0, i, 400, fill="#212F3D")
        for i in range(0, 400, 50): self.canvas_radar.create_line(0, i, 500, i, fill="#212F3D")
        
        # Target Radar
        self.target = self.canvas_radar.create_oval(240, 190, 260, 210, fill="#2ECC71", outline="white", width=2)
        
        btn_reset = tk.Button(radar_frame, text="RESET RADAR POSITION", command=self.reset_radar, 
                              bg="#3498DB", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=20)
        btn_reset.pack(pady=10)

    def reset_radar(self):
        self.virtual_x, self.virtual_y = 250, 200
        self.canvas_radar.coords(self.target, 240, 190, 260, 210)

    def update_loop(self):
        while self.running:
            try:
                if os.path.exists(DEVICE_PATH):
                    fd = os.open(DEVICE_PATH, os.O_RDONLY)
                    data = os.read(fd, 5)
                    os.close(fd)
                    if len(data) == 5:
                        btns, dx, dy, wheel, conn = struct.unpack('BbbbB', data)
                        self.root.after(0, self.update_ui, btns, dx, dy, wheel, conn, data)
                else:
                    self.root.after(0, self.update_ui, 0, 0, 0, 0, 0, None)
            except: pass
            time.sleep(0.01)

    def update_ui(self, btns, dx, dy, wheel, conn, raw_data):
        if conn == 1:
            self.lbl_status.config(text="STATUS: 🟢 KERNEL MODULE ATTACHED", fg="#27AE60", bg="#EAFAF1")
            
            # 1. Cập nhật RAW Hex
            hex_str = " ".join(f"{b:02X}" for b in raw_data)
            self.lbl_raw.config(text=f"RAW: {hex_str}")

            # 2. Cập nhật Radar & Coordinates
            self.virtual_x = max(10, min(490, self.virtual_x + dx * 0.8))
            self.virtual_y = max(10, min(390, self.virtual_y + dy * 0.8))
            self.canvas_radar.coords(self.target, self.virtual_x-10, self.virtual_y-10, self.virtual_x+10, self.virtual_y+10)
            self.lbl_coords.config(text=f"COORD: X={int(self.virtual_x)}, Y={int(self.virtual_y)}")

            # 3. Cập nhật Trạng thái hướng di chuyển
            if dx > 2: self.lbl_dir_x.config(text="H-MOVE: → RIGHT", fg="#2980B9")
            elif dx < -2: self.lbl_dir_x.config(text="H-MOVE: ← LEFT", fg="#2980B9")
            else: self.lbl_dir_x.config(text="H-MOVE: IDLE", fg="#7F8C8D")

            if dy > 2: self.lbl_dir_y.config(text="V-MOVE: ↓ DOWN", fg="#C0392B")
            elif dy < -2: self.lbl_dir_y.config(text="V-MOVE: ↑ UP", fg="#C0392B")
            else: self.lbl_dir_y.config(text="V-MOVE: IDLE", fg="#7F8C8D")

            # 4. Cập nhật Nút bấm hình con chuột
            self.canvas_mouse.itemconfig(self.btn_l, fill="#2ECC71" if btns & 0x01 else "#E5E8E8")
            self.canvas_mouse.itemconfig(self.btn_r, fill="#3498DB" if btns & 0x02 else "#E5E8E8")
            self.canvas_mouse.itemconfig(self.wheel_obj, fill="#F1C40F" if btns & 0x04 else "#95A5A6")

            # 5. Cập nhật mũi tên ▲/▼ khi lăn chuột
            if wheel != 0:
                self.wheel_val = wheel
                self.wheel_timer = 15 # Giữ hiệu ứng 0.15s

            if self.wheel_timer > 0:
                self.wheel_timer -= 1
                if (self.wheel_val > 0 and self.wheel_val < 128) or self.wheel_val < -128: # Lăn lên
                    self.canvas_mouse.itemconfig(self.arr_up, fill="#E74C3C")
                    self.canvas_mouse.itemconfig(self.arr_down, fill="#F2F4F4")
                else: # Lăn xuống
                    self.canvas_mouse.itemconfig(self.arr_up, fill="#F2F4F4")
                    self.canvas_mouse.itemconfig(self.arr_down, fill="#E74C3C")
            else:
                self.canvas_mouse.itemconfig(self.arr_up, fill="#F2F4F4")
                self.canvas_mouse.itemconfig(self.arr_down, fill="#F2F4F4")
        else:
            self.lbl_status.config(text="STATUS: 🔴 KERNEL MODULE DETACHED", fg="#E74C3C", bg="#FDEDEC")
            self.lbl_raw.config(text="RAW: -- -- -- -- --")
            self.lbl_coords.config(text="COORD: X=N/A, Y=N/A")

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseRadarUltimate(root)
    root.mainloop()