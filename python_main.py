import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import serial.tools.list_ports
import serial
import threading
import csv
import time
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HomersekletApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stroboszkóp vezérlő APP")
        self.root.geometry("800x950")
        self.root.configure(bg="#ffffff")

        self.futas = False
        self.kapcsolodva = False
        self.adatok = []
        self.start_idopont = None
        self.soros_port = None
        
        self.checkbox1 = tk.IntVar(value=1)
        self.checkbox2 = tk.IntVar(value=1)
        self.checkbox3 = tk.IntVar(value=1)
        self.checkbox4 = tk.IntVar(value=1)
        self.checkbox_opto = tk.IntVar(value=1)
        self.kivalasztott_port = tk.StringVar()
        self.ventillator_allapot = False

        self.allapot_label = tk.Label(root, text="Nincs csatlakozva", font=("Arial", 14), bg="#ffffff", fg="red")
        self.allapot_label.pack(pady=5)

        # Port választó
        self.port_keret = tk.Frame(root, bg="#ffffff")
        self.port_keret.pack(pady=5)
        tk.Label(self.port_keret, text="Port:", font=("Arial", 12), bg="#ffffff").pack(side=tk.LEFT, padx=5)
        self.port_dropdown = ttk.Combobox(self.port_keret, textvariable=self.kivalasztott_port, state="readonly", width=15)
        self.port_dropdown.pack(side=tk.LEFT, padx=5)
        tk.Button(self.port_keret, text="Frissítés", command=self.portok_keresese).pack(side=tk.LEFT)
        self.connect_btn = tk.Button(self.port_keret, text="Csatlakozás", command=self.csatlakozas_kezeles, bg="lightblue")
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        self.portok_keresese()

        self.ido_label = tk.Label(root, text="Time: 00:00", font=("Arial", 14), bg="#ffffff")
        self.ido_label.pack(pady=5)

        # --- MÓDOSÍTOTT RÉSZ: 4 külön címke a különböző színek miatt ---
        self.data_frame = tk.Frame(root, bg="#ffffff")
        self.data_frame.pack(pady=10)

        self.t1_label = tk.Label(self.data_frame, text="T1: -- °C", font=("Arial", 14), fg="red", bg="#ffffff")
        self.t1_label.grid(row=0, column=0, padx=10, pady=2)

        self.t2_label = tk.Label(self.data_frame, text="T2: -- °C", font=("Arial", 14), fg="#3170f7", bg="#ffffff")
        self.t2_label.grid(row=0, column=1, padx=10, pady=2)

        self.t3_label = tk.Label(self.data_frame, text="T3: -- °C", font=("Arial", 14), fg="green", bg="#ffffff")
        self.t3_label.grid(row=1, column=0, padx=10, pady=2)

        self.t4_label = tk.Label(self.data_frame, text="T4 (Infra): -- °C", font=("Arial", 14), fg="orange", bg="#ffffff")
        self.t4_label.grid(row=1, column=1, padx=10, pady=2)
        # ---------------------------------------------------------------

        # Stroboszkóp paraméterek
        self.param_keret = tk.Frame(root, bg="#ffffff")
        self.param_keret.pack(pady=10, fill=tk.X, padx=20)
        tk.Label(self.param_keret, text="Stroboszkóp Paraméterek", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
        
        inp_f = tk.Frame(self.param_keret, bg="#ffffff")
        inp_f.pack(pady=5)
        tk.Label(inp_f, text="Villanások/ciklus:", bg="#ffffff").grid(row=0, column=0, padx=5)
        self.entry_flashes = tk.Entry(inp_f, width=5)
        self.entry_flashes.insert(0, "5")
        self.entry_flashes.grid(row=0, column=1, padx=5)
        
        tk.Label(inp_f, text="Ciklusok közötti szünet [ms]:", bg="#ffffff").grid(row=0, column=2, padx=5)
        self.entry_interval = tk.Entry(inp_f, width=8)
        self.entry_interval.insert(0, "2000")
        self.entry_interval.grid(row=0, column=3, padx=5)

        tk.Label(inp_f, text="Ciklusok száma:", bg="#ffffff").grid(row=0, column=4, padx=5)
        self.entry_cycles = tk.Entry(inp_f, width=5)
        self.entry_cycles.insert(0, "3")
        self.entry_cycles.grid(row=0, column=5, padx=5)

        # Gombok
        gomb_keret = tk.Frame(root, bg="#ffffff")
        gomb_keret.pack(pady=10)
        self.start_gomb = tk.Button(gomb_keret, text="START Mérés", command=self.start_meres, bg="#00FF08", fg="black", font=("Arial", 16, "bold"), state=tk.DISABLED)
        self.start_gomb.pack(side=tk.LEFT, padx=5)
        self.stop_gomb = tk.Button(gomb_keret, text="RESET / STOP", command=self.stop_meres, bg="#FF1100", fg="black", font=("Arial", 16, "bold"), state=tk.DISABLED)
        self.stop_gomb.pack(side=tk.LEFT, padx=5)
        self.venti_gomb = tk.Button(gomb_keret, text="Ventilátor: KI", command=self.toggle_ventillator, bg="gray", font=("Arial", 16, "bold"), state=tk.DISABLED)
        self.venti_gomb.pack(side=tk.LEFT, padx=5)

        # Checkbox
        self.chechboxholder = tk.Frame(root, bg="#ffffff")
        self.chechboxholder.pack(pady=5)
        tk.Checkbutton(self.chechboxholder, text="T1", variable=self.checkbox1, bg="red", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.chechboxholder, text="T2", variable=self.checkbox2, bg="#3170f7", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.chechboxholder, text="T3", variable=self.checkbox3, bg="green", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.chechboxholder, text="T4", variable=self.checkbox4, bg="orange", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.chechboxholder, text="Opto", variable=self.checkbox_opto, bg="purple", fg="white", selectcolor="purple", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.chechboxholder, text="RESET diag.", command=self.reset_diagramm, bg="#000000", fg="#ffffff", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=15)

        # Diagram
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Idő [s]")
        self.ax.set_ylabel("Hőmérséklet / Opto")
        self.vonal_t1, = self.ax.plot([], [], label="T1", color="red")
        self.vonal_t2, = self.ax.plot([], [], label="T2", color="#3170f7")
        self.vonal_t3, = self.ax.plot([], [], label="T3", color="green")
        self.vonal_t4, = self.ax.plot([], [], label="T4", color="orange")
        self.vonal_opto, = self.ax.plot([], [], label="Opto", color="purple", drawstyle='steps-pre', linewidth=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def portok_keresese(self):
        portok = [port.device for port in serial.tools.list_ports.comports()]
        self.port_dropdown['values'] = portok
        if portok:
            self.kivalasztott_port.set(portok[-1])
        else:
            self.kivalasztott_port.set("Nincs port")

    def csatlakozas_kezeles(self):
    
        if not self.kapcsolodva:

            try:

                self.soros_port = serial.Serial(self.kivalasztott_port.get(), 115200, timeout=0.5)

               

                self.allapot_label.config(text="Csatlakozás", fg="orange")

                self.root.update()

               

                time.sleep(2)

               

                self.soros_port.reset_input_buffer() # port urites

                teszt_sikeres = False

               

                # 3x proba

                for _ in range(3):

                    sor = self.soros_port.readline().decode('utf-8', errors='ignore').strip()

                    # helyes e az adatsor

                    if sor and len(sor.split(',')) == 6:

                        teszt_sikeres = True

                        break

               

                if not teszt_sikeres:

                    self.soros_port.close()

                    messagebox.showerror("Hiba", "A port sikeresen megnyílt, de nem érkezik válasz.\nBiztosan a megfelelő COM portot választottad, és rá van dugva az ESP32?")

                    self.allapot_label.config(text="Nincs csatlakozva", fg="red")

                    return

               

                self.soros_port.timeout = 0.1

                self.kapcsolodva = True

                self.connect_btn.config(text="Bontás", bg="red")

                self.start_gomb.config(state=tk.NORMAL)

                self.venti_gomb.config(state=tk.NORMAL)

                self.allapot_label.config(text="Csatlakozva. Várakozás parancsokra...", fg="green")

               

                # Olvaso thread

                self.thread = threading.Thread(target=self.olvasas_szal, daemon=True)

                self.thread.start()

               

            except Exception as e:

                messagebox.showerror("Hiba", f"Nem sikerült megnyitni a portot: {e}")

                self.allapot_label.config(text="Nincs csatlakozva", fg="red")

        else:

            self.kapcsolodva = False

            self.stop_meres()

            if self.soros_port and self.soros_port.is_open:

                self.soros_port.close()

            self.connect_btn.config(text="Csatlakozás", bg="lightblue")

            self.start_gomb.config(state=tk.DISABLED)

            self.venti_gomb.config(state=tk.DISABLED)

            self.allapot_label.config(text="Nincs csatlakozva", fg="red")



    def toggle_ventillator(self):
        if self.kapcsolodva:
            self.ventillator_allapot = not self.ventillator_allapot
            if self.ventillator_allapot:
                self.soros_port.write(b'F1\n')
                self.venti_gomb.config(text="Ventilátor: BE", bg="cyan")
            else:
                self.soros_port.write(b'F0\n')
                self.venti_gomb.config(text="Ventilátor: KI", bg="gray")

    def olvasas_szal(self):
        while self.kapcsolodva:
            if self.soros_port.in_waiting > 0:
                sor = self.soros_port.readline().decode('utf-8', errors='ignore').strip()
                if sor:
                    self.adat_feldolgozas(sor)
            time.sleep(0.01)

    def adat_feldolgozas(self, sor):
        # CSV forma: millis,T1,T2,T3,T4,Opto
        try:
            reszek = sor.split(',')
            if len(reszek) == 6:
                ido_ms = int(reszek[0])
                t1_val = reszek[1]
                t2_val = reszek[2]
                t3_val = reszek[3]
                t4_val = reszek[4]
                opto_val = reszek[5]

                # --- MÓDOSÍTOTT RÉSZ: 4 külön címke frissítése ---
                self.t1_label.config(text=f"T1: {t1_val} °C")
                self.t2_label.config(text=f"T2: {t2_val} °C")
                self.t3_label.config(text=f"T3: {t3_val} °C")
                self.t4_label.config(text=f"T4 (Infra): {t4_val} °C")
                # --------------------------------------------------

                if self.futas:
                    most = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    try:
                        f_t1 = float(t1_val) if t1_val != "Error" else 0.0
                        f_t2 = float(t2_val) if t2_val != "Error" else 0.0
                        f_t3 = float(t3_val) if t3_val != "Error" else 0.0
                        f_t4 = float(t4_val) if t4_val != "Error" else 0.0

                    except ValueError:
                        return

                    self.adatok.append([most, ido_ms, f_t1, f_t2, f_t3, f_t4, opto_val])
        except Exception:
            pass

    def start_meres(self):
        try:
            flashes = int(self.entry_flashes.get())
            interval = int(self.entry_interval.get())
            cycles = int(self.entry_cycles.get())
        except ValueError:
            messagebox.showerror("Hiba", "Kérlek érvényes számokat adj meg a paramétereknél!")
            return

        self.futas = True
        self.adatok = [] # Rögzítés nullázása
        self.start_idopont = datetime.now()
        
        self.start_gomb.config(state=tk.DISABLED)
        self.stop_gomb.config(state=tk.NORMAL)
        self.allapot_label.config(text="Mérés folyamatban...", fg="orange")
        
        # Parancs küldése az ESP32-nek
        parancs = f"S{flashes},{interval},{cycles}\n"
        self.soros_port.write(parancs.encode())

        self.ido_frissites()
        self.grafikon_frissites()

    def stop_meres(self):
        if self.futas:
            self.futas = False
            self.start_gomb.config(state=tk.NORMAL)
            self.stop_gomb.config(state=tk.DISABLED)
            self.allapot_label.config(text="Mérés leállítva. Csatlakozva.", fg="green")
            
            # Reset parancs kiküldése
            if self.kapcsolodva and self.soros_port.is_open:
                self.soros_port.write(b'X\n')

            self.mentes_fajlba()

    def mentes_fajlba(self):
        if not self.adatok:
            return
        file = f"meres_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["PC_time", "ESP_milis", "T1", "T2", "T3" , "T4", "Opto_Event"])
                writer.writerows(self.adatok)
            messagebox.showinfo("Kész", f"Adatok mentve: {file}")
        except Exception as e:
            messagebox.showerror("Mentési Hiba", str(e))

    def ido_frissites(self):
        if self.futas and self.start_idopont:
            eltelt = datetime.now() - self.start_idopont
            eltelt_str = str(eltelt).split(".")[0]
            self.ido_label.config(text=f"Time: {eltelt_str}")
            self.root.after(1000, self.ido_frissites)

    def grafikon_frissites(self):
        if self.futas:
            utolso_adatok = self.adatok[-1000:] # Utolsó 1000 pont
            
            if utolso_adatok:
                kezdesi_ido = utolso_adatok[0][1]
                x = [(sor[1] - kezdesi_ido)/1000 for sor in utolso_adatok]

                if self.checkbox1.get():
                    self.vonal_t1.set_data(x, [sor[2] for sor in utolso_adatok])
                else: self.vonal_t1.set_data([], [])

                if self.checkbox2.get():
                    self.vonal_t2.set_data(x, [sor[3] for sor in utolso_adatok])
                else: self.vonal_t2.set_data([], [])

                if self.checkbox3.get():
                    self.vonal_t3.set_data(x, [sor[4] for sor in utolso_adatok])
                else: self.vonal_t3.set_data([], [])

                if self.checkbox4.get():
                    self.vonal_t4.set_data(x, [sor[5] for sor in utolso_adatok])
                else: self.vonal_t4.set_data([], [])

                # Opto jel params
                if self.checkbox_opto.get():
                    opto_y = []
                    kitartas = 0
                    for sor in utolso_adatok:
                        val = float(sor[6])
                        if val > 0:
                            kitartas = 1
                        
                        if kitartas > 0:
                            opto_y.append(50) # hol jelenjen meg a jel a grafikonon
                            kitartas -= 1
                        else:
                            opto_y.append(0)
                    self.vonal_opto.set_data(x, opto_y)
                else: 
                    self.vonal_opto.set_data([], [])

                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()

            self.root.after(50, self.grafikon_frissites)

    def reset_diagramm(self):
        self.adatok.clear()
        self.vonal_t1.set_data([], [])
        self.vonal_t2.set_data([], [])
        self.vonal_t3.set_data([], [])
        self.vonal_t4.set_data([], [])
        self.vonal_opto.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = HomersekletApp(root)
    root.mainloop()