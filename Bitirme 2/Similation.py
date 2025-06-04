from ContainerPacking.Packing.Porperties.Item import Item
from ContainerPacking.Packing.Porperties.Container import Container
from ContainerPacking.Packing.Porperties.ContainerPackingResult import ContainerPackingResult
from ContainerPacking.PackingService import PackingService

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.cm as cm

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QLineEdit, QHBoxLayout, QGroupBox, QMessageBox, QListWidget
)


class PackingUI(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_algorithms = []
        self.algorithm_ids = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("3D Container Packing")
        self.setGeometry(100, 100, 1000, 700)
        layout = QVBoxLayout(self)

        # --- PACKING ALGORITHMS ---
        self.algorithms_group = QGroupBox("Packing Algorithms")
        alg_layout = QVBoxLayout()
        self.algorithm_select = QComboBox()
        self.algorithm_select.addItems(["EB-AFIT", "MCTS"])
        self.add_algorithm_btn = QPushButton("+")
        alg_hbox = QHBoxLayout()
        alg_hbox.addWidget(self.add_algorithm_btn)
        alg_hbox.addWidget(self.algorithm_select)
        alg_layout.addLayout(alg_hbox)
        self.algorithm_list_widget = QVBoxLayout()
        alg_layout.addLayout(self.algorithm_list_widget)
        self.algorithms_group.setLayout(alg_layout)
        layout.addWidget(self.algorithms_group)

        # --- ITEMS TO PACK ---
        self.items_group = QGroupBox("Items to Pack")
        items_layout = QVBoxLayout()
        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels(["Name", "L", "W", "H", "Qty"])
        add_item_hbox = QHBoxLayout()
        self.item_name = QLineEdit(); self.item_l = QLineEdit()
        self.item_w = QLineEdit(); self.item_h = QLineEdit()
        self.item_qty = QLineEdit()
        self.add_item_btn = QPushButton("+"); self.delete_item_btn = QPushButton("Delete")
        for w in (self.add_item_btn, self.delete_item_btn,
                  self.item_name, self.item_l, self.item_w, self.item_h, self.item_qty):
            add_item_hbox.addWidget(w)
        items_layout.addLayout(add_item_hbox)
        items_layout.addWidget(self.items_table)
        self.items_group.setLayout(items_layout)
        layout.addWidget(self.items_group)

        # --- CONTAINERS ---
        self.containers_group = QGroupBox("Containers")
        containers_layout = QVBoxLayout()
        self.containers_table = QTableWidget(0, 8)
        self.containers_table.setHorizontalHeaderLabels([
            "Name", "L", "W", "H",
            "Algorithm", "% Cont. Used", "# Packed", "# Unpacked"
        ])
        add_container_hbox = QHBoxLayout()
        self.container_name = QLineEdit(); self.container_l = QLineEdit()
        self.container_w = QLineEdit(); self.container_h = QLineEdit()
        self.add_container_btn = QPushButton("+"); self.delete_container_btn = QPushButton("Delete")
        for w in (self.add_container_btn, self.delete_container_btn,
                  self.container_name, self.container_l, self.container_w, self.container_h):
            add_container_hbox.addWidget(w)
        containers_layout.addLayout(add_container_hbox)
        containers_layout.addWidget(self.containers_table)
        self.containers_group.setLayout(containers_layout)
        layout.addWidget(self.containers_group)

        # --- UNPACKED ITEMS LIST ---
        self.unpacked_group = QGroupBox("Konteynere Yerleşmeyen Öğeler:")
        unpacked_layout = QVBoxLayout()
        self.unpacked_list = QListWidget()
        unpacked_layout.addWidget(self.unpacked_list)
        self.unpacked_group.setLayout(unpacked_layout)
        layout.addWidget(self.unpacked_group)

        # --- PACK BUTTON ---
        self.pack_btn = QPushButton("Pack Em Up")
        layout.addWidget(self.pack_btn)

        # --- SIGNALS ---
        self.add_algorithm_btn.clicked.connect(self.add_algorithm)
        self.add_item_btn.clicked.connect(self.add_item)
        self.delete_item_btn.clicked.connect(self.delete_selected_item)
        self.add_container_btn.clicked.connect(self.add_container)
        self.delete_container_btn.clicked.connect(self.delete_selected_container)
        self.pack_btn.clicked.connect(self.on_pack_clicked)

    def add_algorithm(self):
        alg = self.algorithm_select.currentText()
        if alg in self.selected_algorithms:
            return
        self.selected_algorithms.append(alg)
        hb = QHBoxLayout()
        btn = QPushButton("❌")
        btn.setStyleSheet("background:red;color:white;")
        btn.clicked.connect(lambda _, a=alg, h=hb: self.remove_algorithm(a, h))
        hb.addWidget(btn); hb.addWidget(QLabel(alg))
        self.algorithm_list_widget.addLayout(hb)

    def remove_algorithm(self, alg, hbox):
        if alg in self.selected_algorithms and len(self.selected_algorithms) > 1:
            self.selected_algorithms.remove(alg)
            for i in reversed(range(hbox.count())):
                w = hbox.itemAt(i).widget();
                if w: w.deleteLater()

    def add_item(self):
        name, l, w, h, q = (
            self.item_name.text().strip(),
            self.item_l.text().strip(),
            self.item_w.text().strip(),
            self.item_h.text().strip(),
            self.item_qty.text().strip()
        )
        if not all((name, l, w, h, q)):
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return
        try:
            l, w, h, q = float(l), float(w), float(h), int(q)
        except:
            QMessageBox.warning(self, "Input Error", "Invalid values!")
            return
        r = self.items_table.rowCount();
        self.items_table.insertRow(r)
        for ci, val in enumerate([name, l, w, h, q]):
            self.items_table.setItem(r, ci, QTableWidgetItem(str(val)))

    def delete_selected_item(self):
        r = self.items_table.currentRow()
        if r >= 0: self.items_table.removeRow(r)

    def add_container(self):
        name, l, w, h = (
            self.container_name.text().strip(),
            self.container_l.text().strip(),
            self.container_w.text().strip(),
            self.container_h.text().strip()
        )
        if not all((name, l, w, h)):
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return
        try:
            l, w, h = float(l), float(w), float(h)
        except:
            QMessageBox.warning(self, "Input Error", "Invalid values!")
            return
        r = self.containers_table.rowCount();
        self.containers_table.insertRow(r)
        for ci, val in enumerate([name, l, w, h, ""]):
            self.containers_table.setItem(r, ci, QTableWidgetItem(str(val)))

    def delete_selected_container(self):
        r = self.containers_table.currentRow()
        if r >= 0: self.containers_table.removeRow(r)

    def on_pack_clicked(self):
        if not self.selected_algorithms:
            QMessageBox.warning(self, "Warning", "Select at least one algorithm!")
            return
        if len(self.selected_algorithms) > 1:
            QMessageBox.warning(self, "Warning", "Only one algorithm allowed!")
            return
        alg = self.selected_algorithms[0]
        self.algorithm_ids = [1] if alg == "EB-AFIT" else [2]
        self.pack_containers()

    def pack_containers(self):
        # Oku
        containers, items = [], []
        for r in range(self.containers_table.rowCount()):
            name = self.containers_table.item(r, 0).text()
            l = float(self.containers_table.item(r, 1).text())
            w = float(self.containers_table.item(r, 2).text())
            h = float(self.containers_table.item(r, 3).text())
            containers.append(Container(name, l, w, h))
        for r in range(self.items_table.rowCount()):
            name = self.items_table.item(r, 0).text()
            l = float(self.items_table.item(r, 1).text())
            w = float(self.items_table.item(r, 2).text())
            h = float(self.items_table.item(r, 3).text())
            q = int(self.items_table.item(r, 4).text())
            for _ in range(q):
                items.append(Item(id=r, dim1=l, dim2=w, dim3=h, name=name, quantity=1))

        # Pack
        results = PackingService.pack(containers, items, self.algorithm_ids)

        # Güncelle, simülasyon ve unpacked liste
        self.unpacked_list.clear()
        for idx, res in enumerate(results):
            if not res.algorithm_packing_results:
                continue
            algo = res.algorithm_packing_results[0]
            packed = algo.packed_items
            unpacked = algo.unpacked_items

            # tablo güncelle
            self.containers_table.setItem(idx, 5,
                QTableWidgetItem(f"{algo.percent_container_volume_packed:.2f}%"))
            self.containers_table.setItem(idx, 6,
                QTableWidgetItem(str(len(packed))))
            self.containers_table.setItem(idx, 7,
                QTableWidgetItem(str(len(unpacked))))

            # unpacked öğeleri listeye ekle
            for it in unpacked:
                self.unpacked_list.addItem(it.name)

            # 3D simülasyon
            self.draw_3d_simulation(containers[idx], packed)

    def draw_3d_simulation(self, container, packed_items):
        if not packed_items:
            QMessageBox.information(self, "Simülasyon", "Hiç öğe paketlenmedi.")
            return

        unique = list({it.name for it in packed_items})
        cmap = cm.get_cmap('tab20', len(unique))
        colormap = {name: cmap(i) for i, name in enumerate(unique)}

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # konteyner
        ax.bar3d(0, 0, 0,
                 container.length,
                 container.width,
                 container.height,
                 color='gray', alpha=0.1)

        # öğeler
        for it in packed_items:
            clr = colormap.get(it.name)
            ax.bar3d(it.coord_x, it.coord_y, it.coord_z,
                     it.pack_dim_x, it.pack_dim_y, it.pack_dim_z,
                     color=clr, alpha=0.8)

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(f"Container {container.id}")
        plt.show()


if __name__ == "__main__":
    app = QApplication([])
    window = PackingUI()
    window.show()
    app.exec_()