import sys
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,
    QLabel,QPushButton,QLineEdit,QSpinBox,QComboBox,QListWidget,QListWidgetItem,
    QTableWidget,QTableWidgetItem,QTextEdit,QFileDialog,QMessageBox,QStatusBar
)

class Explorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JASS Parquet Data Explorer")
        self.resize(1500,900)
        self.path=None
        self.pf=None
        self.df=pd.DataFrame()
        self.filtered=pd.DataFrame()
        self.build()
        self.set_dark(True)

    def build(self):
        m=self.menuBar()
        fm=m.addMenu("&File")
        a=QAction("&Open Parquet...",self); a.triggered.connect(self.open); fm.addAction(a)
        a=QAction("&Export CSV...",self); a.triggered.connect(self.export); fm.addAction(a)
        a=QAction("&Quit",self); a.triggered.connect(self.close); fm.addAction(a)
        vm=m.addMenu("&View")
        self.dark=QAction("Dark Mode",self,checkable=True,checked=True)
        self.dark.triggered.connect(lambda:self.set_dark(self.dark.isChecked())); vm.addAction(self.dark)

        root=QWidget(); v=QVBoxLayout(root)
        top=QHBoxLayout()
        t=QLabel("JASS Parquet Data Explorer"); t.setObjectName("title"); top.addWidget(t)
        self.file=QLabel("No Parquet file loaded"); top.addWidget(self.file,1)
        b=QPushButton("📂 Open Parquet"); b.clicked.connect(self.open); top.addWidget(b)
        v.addLayout(top)

        ctl=QHBoxLayout()
        ctl.addWidget(QLabel("Preview rows:"))
        self.limit=QSpinBox(); self.limit.setRange(10,100000); self.limit.setValue(1000); ctl.addWidget(self.limit)
        ctl.addWidget(QLabel("Search:"))
        self.search=QLineEdit(); self.search.setPlaceholderText("Search visible columns..."); self.search.returnPressed.connect(self.filter); ctl.addWidget(self.search,1)
        b=QPushButton("🔎 Search"); b.clicked.connect(self.filter); ctl.addWidget(b)
        b=QPushButton("Clear"); b.clicked.connect(self.clear); ctl.addWidget(b)
        ctl.addWidget(QLabel("Sort:"))
        self.sort=QComboBox(); ctl.addWidget(self.sort)
        b=QPushButton("Sort"); b.clicked.connect(self.sort_rows); ctl.addWidget(b)
        v.addLayout(ctl)

        sp=QSplitter(Qt.Horizontal)
        left=QWidget(); lv=QVBoxLayout(left); lv.addWidget(QLabel("COLUMNS"))
        self.cols=QListWidget(); self.cols.itemChanged.connect(lambda _:self.render()); self.cols.currentItemChanged.connect(self.profile); lv.addWidget(self.cols)
        lv.addWidget(QLabel("DATASET INFO")); self.info=QTextEdit(); self.info.setReadOnly(True); lv.addWidget(self.info); sp.addWidget(left)

        center=QWidget(); cv=QVBoxLayout(center); cv.addWidget(QLabel("DATA PREVIEW"))
        self.table=QTableWidget(); self.table.setSelectionBehavior(QTableWidget.SelectRows); cv.addWidget(self.table)
        self.msg=QLabel("Open a Parquet file to begin."); cv.addWidget(self.msg); sp.addWidget(center)

        right=QWidget(); rv=QVBoxLayout(right); rv.addWidget(QLabel("COLUMN PROFILE"))
        self.prof=QTextEdit(); self.prof.setReadOnly(True); rv.addWidget(self.prof); sp.addWidget(right)
        sp.setSizes([270,900,330]); v.addWidget(sp,1)
        self.setCentralWidget(root); self.setStatusBar(QStatusBar())

    def set_dark(self,on):
        self.setStyleSheet("""QMainWindow,QWidget{background:%s;color:%s}
        QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget{background:%s;color:%s;border:1px solid #394353}
        QPushButton{background:%s;color:%s;padding:7px 12px;border:1px solid #465267;border-radius:5px}
        QHeaderView::section{background:%s;color:%s;padding:6px}
        QLabel#title{font-size:22px;font-weight:700}""" % (
            "#10141c" if on else "#f5f7fa","#e8edf5" if on else "#20242b",
            "#171d27" if on else "#fff","#e8edf5" if on else "#20242b",
            "#263244" if on else "#fff","#f2f5f8" if on else "#20242b",
            "#202838" if on else "#e9edf3","#e8edf5" if on else "#20242b"))

    def open(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Parquet File","","Parquet (*.parquet);;All files (*)")
        if not p:return
        try:self.load(Path(p))
        except Exception as e:QMessageBox.critical(self,"Open failed",str(e))

    def load(self,p):
        self.path=p; self.pf=pq.ParquetFile(p)
        n=self.limit.value()
        # Read only enough row groups to satisfy the preview limit.
        parts=[]; got=0
        for batch in self.pf.iter_batches(batch_size=min(10000,n)):
            parts.append(batch.to_pandas()); got+=len(parts[-1])
            if got>=n:break
        self.df=pd.concat(parts,ignore_index=True).head(n) if parts else pd.DataFrame()
        self.filtered=self.df.copy()
        self.file.setText(str(p))
        self.cols.blockSignals(True); self.cols.clear()
        for f in self.pf.schema_arrow:
            x=QListWidgetItem(f"{f.name}   [{f.type}]"); x.setData(Qt.UserRole,f.name)
            x.setFlags(x.flags()|Qt.ItemIsUserCheckable); x.setCheckState(Qt.Checked); self.cols.addItem(x)
        self.cols.blockSignals(False)
        self.sort.clear(); self.sort.addItems([str(c) for c in self.df.columns])
        md=self.pf.metadata
        self.info.setPlainText("\n".join(
            [f"File: {p.name}",f"Size: {p.stat().st_size/(1024**2):,.2f} MB",
             f"Rows: {md.num_rows:,}",f"Row groups: {md.num_row_groups:,}",
             f"Columns: {len(self.pf.schema_arrow):,}","",
             "SCHEMA"]+[f"• {f.name}: {f.type}" for f in self.pf.schema_arrow]))
        self.render(); self.statusBar().showMessage("Loaded successfully")

    def visible(self):
        return [self.cols.item(i).data(Qt.UserRole) for i in range(self.cols.count()) if self.cols.item(i).checkState()==Qt.Checked]

    def render(self):
        if self.df.empty:return
        cols=[c for c in self.visible() if c in self.filtered.columns]
        self.table.clear(); self.table.setColumnCount(len(cols)); self.table.setRowCount(len(self.filtered))
        self.table.setHorizontalHeaderLabels(cols)
        for r,(_,row) in enumerate(self.filtered[cols].iterrows()):
            for c,val in enumerate(row):
                self.table.setItem(r,c,QTableWidgetItem("" if pd.isna(val) else str(val)))
        self.table.resizeColumnsToContents()
        self.msg.setText(f"{len(self.filtered):,} preview rows • {len(cols):,} visible columns")

    def filter(self):
        q=self.search.text().strip()
        if not q:self.clear();return
        mask=pd.Series(False,index=self.df.index)
        for c in self.visible():
            mask |= self.df[c].astype("string").str.contains(q,case=False,regex=False,na=False)
        self.filtered=self.df.loc[mask].copy(); self.render()

    def clear(self):
        self.search.clear(); self.filtered=self.df.copy(); self.render()

    def sort_rows(self):
        c=self.sort.currentText()
        if c and c in self.filtered:
            try:self.filtered=self.filtered.sort_values(c,kind="stable",na_position="last")
            except Exception:self.filtered=self.filtered.sort_values(c,key=lambda s:s.astype(str),kind="stable")
            self.render()

    def profile(self,item,_):
        if item is None:return
        c=item.data(Qt.UserRole)
        if c not in self.df:return
        s=self.df[c]
        out=[f"COLUMN: {c}",f"Type: {s.dtype}",f"Preview rows: {len(s):,}",f"Nulls: {s.isna().sum():,}",f"Non-null: {s.notna().sum():,}",""]
        if pd.api.types.is_numeric_dtype(s):
            out += ["NUMERIC PROFILE",f"Min: {s.min()}",f"Max: {s.max()}",f"Mean: {s.mean()}"]
        else:
            out += [f"Unique values: {s.nunique(dropna=True):,}","SAMPLE VALUES"]
            out += [f"• {x[:200]}" for x in s.dropna().astype(str).drop_duplicates().head(15)]
        self.prof.setPlainText("\n".join(out))

    def export(self):
        if self.filtered.empty:return
        p,_=QFileDialog.getSaveFileName(self,"Export CSV","","CSV (*.csv)")
        if p:self.filtered[self.visible()].to_csv(p,index=False,encoding="utf-8-sig")

if __name__=="__main__":
    app=QApplication(sys.argv); w=Explorer(); w.show(); sys.exit(app.exec())
