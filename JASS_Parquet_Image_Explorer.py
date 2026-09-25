import sys, io
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QLabel,QPushButton,QLineEdit,QSpinBox,QComboBox,QListWidget,QListWidgetItem,QTableWidget,QTableWidgetItem,QTextEdit,QFileDialog,QMessageBox,QStatusBar

EXTS={".jpg",".jpeg",".png",".webp",".bmp",".gif",".tif",".tiff"}

class App(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("JASS Parquet Image Explorer"); self.resize(1500,900)
        self.path=None; self.pf=None; self.df=pd.DataFrame(); self.filtered=pd.DataFrame(); self.image_col=None
        self.build()
    def build(self):
        root=QWidget(); v=QVBoxLayout(root)
        h=QHBoxLayout(); t=QLabel("JASS Parquet Image Explorer"); t.setObjectName("title"); h.addWidget(t)
        self.file=QLabel("No Parquet file loaded"); h.addWidget(self.file,1)
        b=QPushButton("📂 Open Parquet"); b.clicked.connect(self.open); h.addWidget(b); v.addLayout(h)
        c=QHBoxLayout(); c.addWidget(QLabel("Preview rows:")); self.limit=QSpinBox(); self.limit.setRange(10,100000); self.limit.setValue(1000); c.addWidget(self.limit)
        c.addWidget(QLabel("Search:")); self.search=QLineEdit(); self.search.setPlaceholderText("Search text/metadata..."); self.search.returnPressed.connect(self.filter); c.addWidget(self.search,1)
        b=QPushButton("🔎 Search"); b.clicked.connect(self.filter); c.addWidget(b)
        b=QPushButton("Clear"); b.clicked.connect(self.clear); c.addWidget(b)
        c.addWidget(QLabel("Image column:")); self.img=QComboBox(); self.img.currentTextChanged.connect(self.set_img); c.addWidget(self.img); v.addLayout(c)
        sp=QSplitter(Qt.Horizontal)
        left=QWidget(); lv=QVBoxLayout(left); lv.addWidget(QLabel("COLUMNS")); self.cols=QListWidget(); self.cols.itemChanged.connect(lambda _:self.render()); lv.addWidget(self.cols); lv.addWidget(QLabel("DATASET INFO")); self.info=QTextEdit(); self.info.setReadOnly(True); lv.addWidget(self.info); sp.addWidget(left)
        mid=QWidget(); mv=QVBoxLayout(mid); mv.addWidget(QLabel("DATA + IMAGE")); self.table=QTableWidget(); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.itemSelectionChanged.connect(self.show_image); mv.addWidget(self.table); self.status=QLabel("Open a Parquet file to begin."); mv.addWidget(self.status); sp.addWidget(mid)
        right=QWidget(); rv=QVBoxLayout(right); rv.addWidget(QLabel("IMAGE PREVIEW")); self.preview=QLabel("Select a row"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(300,300); rv.addWidget(self.preview,1); self.imageinfo=QTextEdit(); self.imageinfo.setReadOnly(True); self.imageinfo.setMaximumHeight(140); rv.addWidget(self.imageinfo); b=QPushButton("💾 Save Selected Image"); b.clicked.connect(self.save_image); rv.addWidget(b); sp.addWidget(right); sp.setSizes([260,900,340]); v.addWidget(sp,1)
        self.setCentralWidget(root); self.setStatusBar(QStatusBar())
        self.setStyleSheet("QMainWindow,QWidget{background:#10141c;color:#e8edf5} QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget{background:#171d27;color:#e8edf5;border:1px solid #394353} QPushButton{background:#263244;color:#f2f5f8;padding:7px 12px;border:1px solid #465267;border-radius:5px} QLabel#title{font-size:22px;font-weight:700}")
    def open(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Parquet","","Parquet (*.parquet);;All files (*)")
        if p:
            try:self.load(Path(p))
            except Exception as e:QMessageBox.critical(self,"Open failed",str(e))
    def load(self,p):
        self.path=p; self.pf=pq.ParquetFile(p); n=self.limit.value(); parts=[]; got=0
        for b in self.pf.iter_batches(batch_size=min(5000,n)):
            x=b.to_pandas(); parts.append(x); got+=len(x)
            if got>=n: break
        self.df=pd.concat(parts,ignore_index=True).head(n) if parts else pd.DataFrame(); self.filtered=self.df.copy(); self.file.setText(str(p))
        self.cols.blockSignals(True); self.cols.clear()
        for c in self.df.columns:
            x=QListWidgetItem(str(c)); x.setData(Qt.UserRole,c); x.setFlags(x.flags()|Qt.ItemIsUserCheckable); x.setCheckState(Qt.Checked); self.cols.addItem(x)
        self.cols.blockSignals(False); self.img.blockSignals(True); self.img.clear(); self.img.addItem("(None)")
        for c in self.df.columns:
            s=self.df[c]; name=str(c).lower(); sample=s.dropna().head(10)
            if "image" in name or "img" in name or any(self.is_image(x) for x in sample): self.img.addItem(str(c))
        self.img.blockSignals(False)
        if self.img.count()>1:self.img.setCurrentIndex(1)
        md=self.pf.metadata; schema=self.pf.schema_arrow
        self.info.setPlainText("\n".join([f"File: {p.name}",f"Size: {p.stat().st_size/(1024**2):,.2f} MB",f"Rows: {md.num_rows:,}",f"Row groups: {md.num_row_groups:,}",f"Columns: {len(schema):,}","SCHEMA"]+[f"• {f.name}: {f.type}" for f in schema])); self.render()
    def is_image(self,v):
        if isinstance(v,(bytes,bytearray,memoryview)): return True
        if isinstance(v,dict): return any(k in v for k in ("bytes","data","path"))
        return isinstance(v,str) and Path(v).suffix.lower() in EXTS
    def set_img(self,t): self.image_col=None if t=="(None)" else t; self.render()
    def visible(self): return [self.cols.item(i).data(Qt.UserRole) for i in range(self.cols.count()) if self.cols.item(i).checkState()==Qt.Checked]
    def render(self):
        if self.filtered.empty:return
        cols=self.visible(); self.table.clear(); self.table.setColumnCount(len(cols)); self.table.setRowCount(len(self.filtered)); self.table.setHorizontalHeaderLabels([str(x) for x in cols])
        for r,(_,row) in enumerate(self.filtered[cols].iterrows()):
            for c,col in enumerate(cols):
                val=row[col]; self.table.setItem(r,c,QTableWidgetItem("🖼 IMAGE" if col==self.image_col else ("" if pd.isna(val) else str(val))))
        self.table.resizeColumnsToContents(); self.status.setText(f"{len(self.filtered):,} preview rows • select a row to view its image")
    def filter(self):
        q=self.search.text().strip()
        if not q:return self.clear()
        mask=pd.Series(False,index=self.df.index)
        for c in self.visible():
            if c!=self.image_col: mask|=self.df[c].astype("string").str.contains(q,case=False,regex=False,na=False)
        self.filtered=self.df.loc[mask].copy(); self.render()
    def clear(self): self.search.clear(); self.filtered=self.df.copy(); self.render()
    def value(self):
        rows=self.table.selectionModel().selectedRows()
        return None if not rows or not self.image_col else self.filtered.iloc[rows[0].row()][self.image_col]
    def pix(self,v):
        if isinstance(v,dict): v=v.get("bytes",v.get("data",v.get("path")))
        if isinstance(v,(bytes,bytearray,memoryview)):
            p=QPixmap(); raw=bytes(v); return (p,raw) if p.loadFromData(raw) else (None,raw)
        if isinstance(v,str):
            pth=Path(v); pth=pth if pth.is_absolute() else self.path.parent/pth
            if pth.exists():
                p=QPixmap(str(pth)); return (p,None) if not p.isNull() else (None,None)
        return None,None
    def show_image(self):
        p,raw=self.pix(self.value())
        if p is None:self.preview.setText("No renderable image"); self.imageinfo.setPlainText("The selected value is not a renderable image or its path was not found."); return
        self.preview.setPixmap(p.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)); self.imageinfo.setPlainText(f"Size: {p.width()} × {p.height()} pixels"+(f"\nEmbedded bytes: {len(raw):,}" if raw else ""))
    def save_image(self):
        p,_=self.pix(self.value())
        if p is None:return QMessageBox.information(self,"No image","Select a row containing an image.")
        out,_=QFileDialog.getSaveFileName(self,"Save Image","","PNG (*.png);;JPEG (*.jpg)")
        if out and not p.save(out): QMessageBox.warning(self,"Save failed","Could not save the image.")

if __name__=="__main__":
    app=QApplication(sys.argv); w=App(); w.show(); sys.exit(app.exec())
