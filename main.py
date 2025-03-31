import tkinter as tk
from gerenciador_bloqueio import GerenciadorBloqueios

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorBloqueios(root)
    root.mainloop() 