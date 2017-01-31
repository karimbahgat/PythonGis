
import pythongis as pg
import tk2


class LoadDataDialog(tk2.Window):
    def __init__(self, master=None, filepath=""):
        tk2.Window.__init__(self, master)

        title = tk2.Label(self, text="Load File:")
        title.pack()

        filearea = tk2.Frame(self)
        filearea.pack(fill="both", expand=1)

        self.filepath = tk2.basics.Entry(filearea, default=filepath, label="Filepath")
        self.filepath.pack(side="left", fill="x", expand=1)

        def browse():
            fp = tk2.filedialog.askopenfilename()
            if fp:
                self.filepath.set(fp)
        self.browsebut = tk2.basics.Button(filearea, text="Browse", command=browse)
        self.browsebut.pack(side="right")

        optionsarea = tk2.Frame(self)
        optionsarea.pack(fill="both", expand=1)

        self.encoding = tk2.basics.Dropdown(optionsarea, label="Encoding", values=["latin","utf8"])
        self.encoding.set("latin")
        self.encoding.pack()

        butarea = tk2.Frame(self)
        butarea.pack()
        
        def ok():
            self.load()
            self.destroy()
        self.okbut = tk2.basics.OkButton(self, command=ok)
        self.okbut.pack(side="right")
        def cancel():
            self.destroy()
        self.cancelbut = tk2.basics.CancelButton(self, command=cancel)
        self.cancelbut.pack(side="left")

    def load(self):
        # TODO: should prob be threaded
        filepath = self.filepath.get()
        data = None
        for typ in pg.vector.loader.file_extensions:
            if filepath.endswith(typ):
                data = pg.VectorData(filepath, encoding=self.encoding.get())
                break
        for typ in pg.raster.loader.file_extensions:
            if filepath.endswith(typ):
                data = pg.RasterData(filepath)
                break
            
        self.onsuccess(data)
        
