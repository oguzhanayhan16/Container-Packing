from ContainerPacking.Packing.Algorithms.PackingAlgorithm import PackingAlgorithm
from ContainerPacking.Packing.Porperties.Item import Item
from ContainerPacking.Packing.Porperties.PackingResult import AlgorithmPackingResult
from collections import defaultdict


class EB_AFIT(PackingAlgorithm):
    def __init__(self):
        # Liste ve temel değişkenler
        self.items_to_pack = []  # Paketlenecek öğelerin listesi
        self.items_packed_in_order = []  # Paketlenen öğelerin sırası
        self.layers = []  # Katmanlar
        self.result = None

        # Flaglar ve durumlar
        self.quit = False
        self.evened = False
        self.hundred_percent_packed = False
        self.layer_done = False
        self.packing = False
        self.packing_best = False

        # Geometrik değişkenler
        self.px = 0.0
        self.py = 0.0
        self.pz = 0.0
        self.remainpy = 0.0
        self.remainpz = 0.0
        self.layer_thickness = 0.0

        # Volümetrik hesaplamalar
        self.packed_volume = 0.0
        self.total_item_volume = 0.0
        self.total_container_volume = 0.0

        # En iyi çözüm bilgileri

        self.best_variant = 0
        self.best_iteration = 0

        self.prelayer = 0
        self.prepackedy = 0
        self.preremainpy = 0

        # Diğer yardımcı değişkenler
        self.layerinlayer = 0.0
        self.bboxi = 0
        self.boxi = 0
        self.cboxi = 0
        self.layer_list_len = 0
        self.packed_item_count = 0
        self.items_to_pack_count = 0
        self.x = 0

        self.items_to_pack_count = len(self.items_to_pack)
        # Box bilgileri
        self.boxx = self.boxy = self.boxz = 0.0
        self.bfx = self.bfy = self.bfz = float('inf')
        self.bboxx = self.bboxy = self.bboxz = 0.0
        self.bbfx = self.bbfy = self.bbfz = float('inf')
        self.cboxx = self.cboxy = self.cboxz = 0.0

        # Yardımcı sınıflar
        self.trash = ScrapPad()
        self.scrapfirst = ScrapPad()  # ScrapPad sınıfını tanımlamanız gerekiyor
        self.smallestZ = ScrapPad()
        # Diğer fonksiyonlar burada olacak

    def run(self, container, items):
        try:
            self.initialize(container, items)
            self.execute_iterations(container)
            self.report(container)

            result = AlgorithmPackingResult(
                algorithm_id=1,  # Algoritma ID'si
                algorithm_name="EB-AFIT",  # Algoritma adı
                is_complete_pack=False  # Paketleme durumu
            )

        except Exception as e:
            print(f"Bir hata oluştu: {e}")
            return None

        try:
            for i in range(1, int(self.items_to_pack_count) + 1):  # 0 tabanlı indeksleme
                item = self.items_to_pack[i]  # self.items_to_pack[i] kontrol ediliyor
                if not item.is_packed:  # IsPacked özelliğine erişim
                    result.unpacked_items.append(item)

        except IndexError as e:
            print(f"IndexError: {e} - self.items_to_pack count: {len(self.items_to_pack)}")
        except AttributeError as e:
            print(f"AttributeError: {e} - self.items_to_pack[{i}] does not have the required attributes")
        except Exception as e:
            print(f"Unexpected error: {e}")

        result.packed_items = self.items_packed_in_order

        if len(result.unpacked_items) == 0:
            result.is_complete_pack = True  # Burada `True` ile işaretlenmeli

        return result

    def analyze_box(self, hmx, hy, hmy, hz, hmz, dim1, dim2, dim3):
        if dim1 <= hmx and dim2 <= hmy and dim3 <= hmz:
            if dim2 <= hy:
                if hy - dim2 < self.bfy:
                    self.boxx = dim1
                    self.boxy = dim2
                    self.boxz = dim3
                    self.bfx = hmx - dim1
                    self.bfy = hy - dim2
                    self.bfz = abs(hz - dim3)
                    self.boxi = self.x
                elif hy - dim2 == self.bfy and hmx - dim1 < self.bfx:
                    self.boxx = dim1
                    self.boxy = dim2
                    self.boxz = dim3
                    self.bfx = hmx - dim1
                    self.bfy = hy - dim2
                    self.bfz = abs(hz - dim3)
                    self.boxi = self.x
                elif hy - dim2 == self.bfy and hmx - dim1 == self.bfx and abs(hz - dim3) < self.bfz:
                    self.boxx = dim1
                    self.boxy = dim2
                    self.boxz = dim3
                    self.bfx = hmx - dim1
                    self.bfy = hy - dim2
                    self.bfz = abs(hz - dim3)
                    self.boxi = self.x
            else:
                if dim2 - hy < self.bbfy:
                    self.bboxx = dim1
                    self.bboxy = dim2
                    self.bboxz = dim3
                    self.bbfx = hmx - dim1
                    self.bbfy = dim2 - hy
                    self.bbfz = abs(hz - dim3)
                    self.bboxi = self.x
                elif dim2 - hy == self.bbfy and hmx - dim1 < self.bbfx:
                    self.bboxx = dim1
                    self.bboxy = dim2
                    self.bboxz = dim3
                    self.bbfx = hmx - dim1
                    self.bbfy = dim2 - hy
                    self.bbfz = abs(hz - dim3)
                    self.bboxi = self.x
                elif dim2 - hy == self.bbfy and hmx - dim1 == self.bbfx and abs(hz - dim3) < self.bbfz:
                    self.bboxx = dim1
                    self.bboxy = dim2
                    self.bboxz = dim3
                    self.bbfx = hmx - dim1
                    self.bbfy = dim2 - hy
                    self.bbfz = abs(hz - dim3)
                    self.bboxi = self.x

    def check_found(self):
        self.evened = False
        if self.boxi != 0:
            self.cboxi = self.boxi
            self.cboxx = self.boxx
            self.cboxy = self.boxy
            self.cboxz = self.boxz
        else:
            if self.bboxi > 0 and (
                    self.layerinlayer != 0 or (self.smallestZ.pre is None and self.smallestZ.post is None)):
                if self.layerinlayer == 0:
                    self.prelayer = self.layer_thickness
                    self.lilz = self.smallestZ.cum_z
                self.cboxi = self.bboxi
                self.cboxx = self.bboxx
                self.cboxy = self.bboxy
                self.cboxz = self.bboxz
                self.layerinlayer = self.layerinlayer + self.bboxy - self.layer_thickness
                self.layer_thickness = self.bboxy
            else:
                if self.smallestZ.pre is None and self.smallestZ.post is None:
                    self.layerDone = True
                else:
                    self.evened = True
                    if self.smallestZ.pre is None:
                        self.trash = self.smallestZ.post
                        self.smallestZ.cum_x = self.smallestZ.post.cum_x
                        self.smallestZ.cum_z = self.smallestZ.post.cum_z
                        self.smallestZ.post = self.smallestZ.post.post
                        if self.smallestZ.post is not None:
                            self.smallestZ.post.pre = self.smallestZ
                    elif self.smallestZ.post is None:
                        self.smallestZ.pre.post = None
                        self.smallestZ.pre.cum_x = self.smallestZ.cum_x
                    else:
                        if self.smallestZ.pre.cum_z == self.smallestZ.post.cum_z:
                            self.smallestZ.pre.post = self.smallestZ.post.post
                            if self.smallestZ.post.post is not None:
                                self.smallestZ.post.post.pre = self.smallestZ.pre
                            self.smallestZ.pre.cum_x = self.smallestZ.post.cum_x
                        else:
                            self.smallestZ.pre.post = self.smallestZ.post
                            self.smallestZ.post.pre = self.smallestZ.pre
                            if self.smallestZ.pre.cum_z < self.smallestZ.post.cum_z:
                                self.smallestZ.pre.cum_x = self.smallestZ.cum_x

    def execute_iterations(self, container):
        bestVolume = 0.0

        for containerOrientationVariant in range(1, 7):
            # print(f"Processing orientation {containerOrientationVariant}")
            if self.quit:
                break
            if containerOrientationVariant == 1:
                self.px, self.py, self.pz = container.length, container.height, container.width
            elif containerOrientationVariant == 2:
                self.px, self.py, self.pz = container.width, container.height, container.length
            elif containerOrientationVariant == 3:
                self.px, self.py, self.pz = container.width, container.length, container.height
            elif containerOrientationVariant == 4:
                self.px, self.py, self.pz = container.height, container.length, container.width
            elif containerOrientationVariant == 5:
                self.px, self.py, self.pz = container.length, container.width, container.height
            elif containerOrientationVariant == 6:
                self.px, self.py, self.pz = container.height, container.width, container.length

            self.layers.append({'layer_eval': -1, 'layer_dim': 0})
            self.list_candit_layers()  # Bu fonksiyon eksik, burada katmanlarınızı listelemelisiniz
            self.layers = sorted(self.layers, key=lambda l: l['layer_eval'])
            for layersIndex in range(1, self.layerListLen + 1):
                if self.quit:
                    break
                # print(f"Processing layer {layersIndex}")

                self.packed_volume = 0.0
                self.packedy = 0
                self.packing = True
                self.layer_thickness = self.layers[layersIndex]['layer_dim']
                itelayer = layersIndex
                self.remainpy = self.py
                self.remainpz = self.pz
                self.packedItemCount = 0

                # Paketlenmemiş öğeleri işaretleyin
                # self.items_to_pack_count = len(self.items_to_pack)
                try:
                    # range(0, self.items_to_pack_count) kullanarak index'leri doğru aralıkta kullanın
                    for x in range(1, self.items_to_pack_count + 1):
                        self.items_to_pack[x].is_packed = False
                except Exception as e:
                    print(f"Error during the for loop: {e}")

                # Katman paketleme döngüsü
                while self.packing and not self.quit:
                    # print("Packing layer...")
                    self.layerinlayer = 0
                    self.layerDone = False

                    self.pack_layer()  # Burasıda tamam

                    # Katman boyutları güncelleniyor
                    self.packedy += self.layer_thickness
                    self.remainpy = self.py - self.packedy

                    # Katman içinde öğeler bulunuyorsa, ek işlemler yapılır
                    # print(f"self.layerinlayer: {self.layerinlayer}, self.quit: {self.quit}")
                    if self.layerinlayer != 0 and not self.quit:
                        self.prepackedy = self.packedy
                        self.preremainpy = self.remainpy
                        self.remainpy = self.layer_thickness - self.prelayer
                        self.packedy = self.packedy - self.layer_thickness + self.prelayer
                        self.remainpz = self.lilz
                        self.layer_thickness = self.layerinlayer
                        self.layerDone = False

                        self.pack_layer()  # Bu fonksiyon tekrar çağrılıyor

                        # Önceki değerler geri alınır
                        self.packedy = self.prepackedy
                        self.remainpy = self.preremainpy
                        self.remainpz = self.pz

                    self.find_layer(self.remainpy)  # Bu fonksiyon eksik, burada katmanları bulmalısınız

                # Eğer yeni bir en iyi hacim bulunduysa, bunu kaydedin
                if self.packed_volume > bestVolume and not self.quit:
                    bestVolume = self.packed_volume
                    self.best_variant = containerOrientationVariant
                    self.best_iteration = itelayer

                # Eğer yüzde 100 paketlenmişse döngüden çıkın
                if self.hundred_percent_packed:
                    # print("Container packed 100%!")
                    break

            # Eğer yüzde 100 paketlenmişse dışarı çıkın
            if self.hundred_percent_packed:
                # print("Container fully packed.")
                break

            # Eğer konteyner kare şeklindeyse, başka bir yönlemeye geçme
            if container.length == container.height == container.width:
                containerOrientationVariant = 6

                # Katmanlar sıfırlanır
            self.layers = []

    def find_box(self, hmx, hy, hmy, hz, hmz):
        self.bfx = self.bfy = self.bfz = 32767
        self.bbfx = self.bbfy = self.bbfz = 32767
        self.boxi = 0
        self.bboxi = 0

        y = 1
        while y < self.items_to_pack_count + 1:
            quantity = self.items_to_pack[y].total_quantity
            # print(f"y: {y}, quantity: {quantity}")  # Debug
            self.x = y

            # for x in range(y, self.x + quantity):
            #     self.x = x
            #     if not self.items_to_pack[x].is_packed:
            #         break
            x = y
            while x < x + quantity - 1:  # 🔹 self.x ile koşulu düzelttim

                if not self.items_to_pack[x].is_packed:
                    break
                x += 1
            self.x = x
            if self.items_to_pack[self.x].is_packed:
                # print("Continue: Zaten paketlenmiş")
                y += self.items_to_pack[y].total_quantity  # **Burada atlama yap!**
                continue

            if self.x > self.items_to_pack_count:
                # print(f"Return: self.x ({self.x}) >= self.items_to_pack_count ({self.items_to_pack_count})")
                return

            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim1,
                             self.items_to_pack[self.x].dim2,
                             self.items_to_pack[self.x].dim3)

            if self.items_to_pack[self.x].dim1 == self.items_to_pack[self.x].dim3 == self.items_to_pack[self.x].dim2:
                y += self.items_to_pack[y].total_quantity  # **Burada da unutma!**
                continue

            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim1,
                             self.items_to_pack[self.x].dim3,
                             self.items_to_pack[self.x].dim2)
            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim2,
                             self.items_to_pack[self.x].dim1,
                             self.items_to_pack[self.x].dim3)
            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim2,
                             self.items_to_pack[self.x].dim3,
                             self.items_to_pack[self.x].dim1)
            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim3,
                             self.items_to_pack[self.x].dim1,
                             self.items_to_pack[self.x].dim2)
            self.analyze_box(hmx, hy, hmy, hz, hmz,
                             self.items_to_pack[self.x].dim3,
                             self.items_to_pack[self.x].dim2,
                             self.items_to_pack[self.x].dim1)

            y += self.items_to_pack[y].total_quantity

    def find_layer(self, thickness):
        exdim = dimen2 = dimen3 = 0
        dimdif = 0
        eval = 1000000
        self.layer_thickness = 0

        for self.x in range(1, self.items_to_pack_count + 1):
            if self.items_to_pack[self.x].is_packed:
                continue

            for y in range(1, 4):
                if y == 1:
                    exdim = self.items_to_pack[self.x].dim1
                    dimen2 = self.items_to_pack[self.x].dim2
                    dimen3 = self.items_to_pack[self.x].dim3
                elif y == 2:
                    exdim = self.items_to_pack[self.x].dim2
                    dimen2 = self.items_to_pack[self.x].dim1
                    dimen3 = self.items_to_pack[self.x].dim3
                elif y == 3:
                    exdim = self.items_to_pack[self.x].dim3
                    dimen2 = self.items_to_pack[self.x].dim1
                    dimen3 = self.items_to_pack[self.x].dim2

                layer_eval = 0

                if exdim <= thickness and (
                        (dimen2 <= self.px and dimen3 <= self.pz) or (dimen3 <= self.px and dimen2 <= self.pz)):
                    for z in range(1, self.items_to_pack_count + 1):
                        if self.x != z and not self.items_to_pack[z].is_packed:
                            dimdif = abs(exdim - self.items_to_pack[z].dim1)
                            dimdif = min(dimdif, abs(exdim - self.items_to_pack[z].dim2))
                            dimdif = min(dimdif, abs(exdim - self.items_to_pack[z].dim3))
                            layer_eval += dimdif

                    if layer_eval < eval:
                        eval = layer_eval
                        self.layer_thickness = exdim

        if self.layer_thickness == 0 or self.layer_thickness > self.remainpy:
            self.packing = False

    def find_smallestZ(self):
        scrapmemb = self.scrap_first
        self.smallestZ = scrapmemb

        while scrapmemb.post is not None:
            if scrapmemb.post.cum_z < self.smallestZ.cum_z:
                self.smallestZ = scrapmemb.post
            scrapmemb = scrapmemb.post

    def initialize(self, container, items):
        self.items_to_pack = []
        self.items_packed_in_order = []
        self.result = None

        self.items_to_pack.append(Item(0, 0, 0, 0, 0, 0))
        self.layers = []
        self.items_to_pack_count = 0

        # Aynı ID'li item'lerin toplam miktarını hesapla
        total_quantity_map = defaultdict(int)
        for item in items:
            total_quantity_map[item.id] += item.quantity

        for item in items:
            for _ in range(item.quantity):
                new_item = Item(item.id, item.dim1, item.dim2, item.dim3, item.name, quantity=1,
                                total_quantity=total_quantity_map[item.id])  # Her kopya için quantity=1
                self.items_to_pack.append(new_item)

            self.items_to_pack_count += item.quantity
        self.items_to_pack.append(Item(0, 0, 0, 0, 0, 0))
        self.total_container_volume = container.length * container.height * container.width
        self.total_item_volume = sum(item.volume for item in self.items_to_pack[1:])

        self.scrap_first = ScrapPad()
        self.scrap_first.pre = None
        self.scrap_first.post = None
        self.packing_best = False
        self.hundred_percent_packed = False
        self.quit = False

    def list_candit_layers(self):
        exdim = 0
        dimdif = 0
        dimen2 = 0
        dimen3 = 0
        layer_eval = 0

        self.layerListLen = 0

        try:
            for x in range(1, self.items_to_pack_count + 1):
                for y in range(1, 4):
                    if y == 1:
                        exdim = self.items_to_pack[x].dim1
                        dimen2 = self.items_to_pack[x].dim2
                        dimen3 = self.items_to_pack[x].dim3
                    elif y == 2:
                        exdim = self.items_to_pack[x].dim2
                        dimen2 = self.items_to_pack[x].dim1
                        dimen3 = self.items_to_pack[x].dim3
                    elif y == 3:
                        exdim = self.items_to_pack[x].dim3
                        dimen2 = self.items_to_pack[x].dim1
                        dimen3 = self.items_to_pack[x].dim2

                    if (exdim > self.py) or (
                            ((dimen2 > self.px or dimen3 > self.pz) and (dimen3 > self.px or dimen2 > self.pz))):
                        continue

                    same = False
                    # print("Layers List:", self.layers)
                    for k in range(1, self.layerListLen + 1):
                        #   print(f"Checking layer {k}: {self.layers[k]}")
                        try:
                            if exdim == self.layers[k]['layer_dim']:
                                same = True
                                break
                        except KeyError as e:
                            print(f"KeyError: 'layer_dim' anahtarı mevcut değil, hata koda girilen k değeri ile: {k}")
                        except Exception as e:
                            print(f"Beklenmeyen bir hata oluştu: {str(e)}")
                    if same:
                        continue

                        # layer_eval hesaplama kısmı
                    layer_eval = 0
                    for z in range(1, self.items_to_pack_count + 1):
                        if x != z:
                            dimdif = abs(exdim - self.items_to_pack[z].dim1)

                            if abs(exdim - self.items_to_pack[z].dim2) < dimdif:
                                dimdif = abs(exdim - self.items_to_pack[z].dim2)
                            if abs(exdim - self.items_to_pack[z].dim3) < dimdif:
                                dimdif = abs(exdim - self.items_to_pack[z].dim3)

                            layer_eval += dimdif

                    # Yeni bir katman ekleniyor
                    self.layerListLen += 1
                    self.layers.append({'layer_dim': exdim, 'layer_eval': layer_eval})  # Layer nesnesi ekleniyor
        except Exception as e:
            print(f"An error occurred: {e}")

    def output_box_list(self):
        try:
            # Koordinat ve boyut değişkenlerini başlat
            pack_coord_x = 0
            pack_coord_y = 0
            pack_coord_z = 0
            pack_dim_x = 0
            pack_dim_y = 0
            pack_dim_z = 0

            # İşlem yapılacak item
            item = self.items_to_pack[self.cboxi]

            # En iyi varyanta göre koordinat ve boyutları belirle
            if self.best_variant == 1:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_x, item.coord_y, item.coord_z
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_x, item.pack_dim_y, item.pack_dim_z
            elif self.best_variant == 2:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_z, item.coord_y, item.coord_x
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_z, item.pack_dim_y, item.pack_dim_x
            elif self.best_variant == 3:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_y, item.coord_z, item.coord_x
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_y, item.pack_dim_z, item.pack_dim_x
            elif self.best_variant == 4:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_y, item.coord_x, item.coord_z
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_y, item.pack_dim_x, item.pack_dim_z
            elif self.best_variant == 5:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_x, item.coord_z, item.coord_y
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_x, item.pack_dim_z, item.pack_dim_y
            elif self.best_variant == 6:
                pack_coord_x, pack_coord_y, pack_coord_z = item.coord_z, item.coord_x, item.coord_y
                pack_dim_x, pack_dim_y, pack_dim_z = item.pack_dim_z, item.pack_dim_x, item.pack_dim_y

            # Güncellenmiş değerleri item nesnesine ata
            item.coord_x = pack_coord_x
            item.coord_y = pack_coord_y
            item.coord_z = pack_coord_z
            item.pack_dim_x = pack_dim_x
            item.pack_dim_y = pack_dim_y
            item.pack_dim_z = pack_dim_z

            # Güncellenmiş item'i listeye ekle
            self.items_packed_in_order.append(item)

        except IndexError as e:
            print(
                f"IndexError: {e} - self.cboxi değeri {self.cboxi}, ancak items_to_pack listesinde yeterli eleman yok.")
        except AttributeError as e:
            print(f"AttributeError: {e} - item nesnesinde beklenen bir özellik eksik olabilir.")
        except Exception as e:
            print(f"Bilinmeyen bir hata oluştu: {e}")

    def pack_layer(self):
        if self.layer_thickness == 0:
            self.packing = False
            return

        self.scrap_first.cum_x = self.px
        self.scrap_first.cum_z = 0

        while not self.quit:
            self.find_smallestZ()

            if self.smallestZ.pre is None and self.smallestZ.post is None:
                # *** DURUM-1: SAĞ VE SOLDA KUTU YOK ***

                lenx = self.smallestZ.cum_x
                lpz = self.remainpz - self.smallestZ.cum_z
                self.find_box(lenx, self.layer_thickness, self.remainpy, lpz, lpz)

                self.check_found()

                if self.layerDone:
                    break
                if self.evened:
                    continue

                self.items_to_pack[self.cboxi].coord_x = 0
                self.items_to_pack[self.cboxi].coord_y = self.packedy
                self.items_to_pack[self.cboxi].coord_z = self.smallestZ.cum_z

                if self.cboxx == self.smallestZ.cum_x:
                    self.smallestZ.cum_z += self.cboxz
                else:
                    self.smallestZ.post = ScrapPad()
                    self.smallestZ.post.post = None
                    self.smallestZ.post.pre = self.smallestZ
                    self.smallestZ.post.cum_x = self.smallestZ.cum_x
                    self.smallestZ.post.cum_z = self.smallestZ.cum_z
                    self.smallestZ.cum_x = self.cboxx
                    self.smallestZ.cum_z += self.cboxz

            elif self.smallestZ.pre is None:
                # *** DURUM-2: SOLDA KUTU YOK ***

                lenx = self.smallestZ.cum_x
                lenz = self.smallestZ.post.cum_z - self.smallestZ.cum_z
                lpz = self.remainpz - self.smallestZ.cum_z
                self.find_box(lenx, self.layer_thickness, self.remainpy, lenz, lpz)
                self.check_found()

                if self.layerDone:
                    break
                if self.evened:
                    continue

                self.items_to_pack[self.cboxi].coord_y = self.packedy
                self.items_to_pack[self.cboxi].coord_z = self.smallestZ.cum_z

                if self.cboxx == self.smallestZ.cum_x:
                    self.items_to_pack[self.cboxi].coord_x = 0

                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.post.cum_z:
                        self.smallestZ.cum_z = self.smallestZ.post.cum_z
                        self.smallestZ.cum_x = self.smallestZ.post.cum_x
                        self.trash = self.smallestZ.post
                        self.smallestZ.post = self.smallestZ.post.post

                        if self.smallestZ.post is not None:
                            self.smallestZ.post.pre = self.smallestZ
                    else:
                        self.smallestZ.cum_z += self.cboxz
                else:
                    self.items_to_pack[self.cboxi].coord_x = self.smallestZ.cum_x - self.cboxx

                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.post.cum_z:
                        self.smallestZ.cum_x -= self.cboxx
                    else:
                        self.smallestZ.post.pre = ScrapPad()

                        self.smallestZ.post.pre.post = self.smallestZ.post
                        self.smallestZ.post.pre.pre = self.smallestZ
                        self.smallestZ.post = self.smallestZ.post.pre
                        self.smallestZ.post.cum_x = self.smallestZ.cum_x
                        self.smallestZ.cum_x -= self.cboxx
                        self.smallestZ.post.cum_z = self.smallestZ.cum_z + self.cboxz

            elif self.smallestZ.post is None:
                # *** DURUM-3: SAĞDA KUTU YOK ***

                lenx = self.smallestZ.cum_x - self.smallestZ.pre.cum_x
                lenz = self.smallestZ.pre.cum_z - self.smallestZ.cum_z
                lpz = self.remainpz - self.smallestZ.cum_z
                self.find_box(lenx, self.layer_thickness, self.remainpy, lenz, lpz)
                self.check_found()

                if self.layerDone:
                    break
                if self.evened:
                    continue

                self.items_to_pack[self.cboxi].coord_y = self.packedy
                self.items_to_pack[self.cboxi].coord_z = self.smallestZ.cum_z
                self.items_to_pack[self.cboxi].coord_x = self.smallestZ.pre.cum_x

                if self.cboxx == self.smallestZ.cum_x - self.smallestZ.pre.cum_x:
                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.pre.cum_z:
                        self.smallestZ.pre.cum_x = self.smallestZ.cum_x
                        self.smallestZ.pre.post = None
                    else:
                        self.smallestZ.cum_z += self.cboxz
                else:
                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.pre.cum_z:
                        self.smallestZ.pre.cum_x += self.cboxx
                    else:
                        self.smallestZ.pre.post = ScrapPad()

                        self.smallestZ.pre.post.pre = self.smallestZ.pre
                        self.smallestZ.pre.post.post = self.smallestZ
                        self.smallestZ.pre = self.smallestZ.pre.post
                        self.smallestZ.pre.cum_x = self.smallestZ.pre.pre.cum_x + self.cboxx
                        self.smallestZ.pre.cum_z = self.smallestZ.cum_z + self.cboxz
                        # Other situations need to be converted similarly
                        # ...
            elif self.smallestZ.pre.cum_z == self.smallestZ.post.cum_z:

                lenx = self.smallestZ.cum_x - self.smallestZ.pre.cum_x
                lenz = self.smallestZ.pre.cum_z - self.smallestZ.cum_z
                lpz = self.remainpz - self.smallestZ.cum_z

                self.find_box(lenx, self.layer_thickness, self.remainpy, lenz, lpz)
                self.check_found()

                if self.layerDone:
                    break
                if self.evened:
                    continue

                self.items_to_pack[self.cboxi].coord_y = self.packedy
                self.items_to_pack[self.cboxi].coord_z = self.smallestZ.cum_z

                if self.cboxx == self.smallestZ.cum_x - self.smallestZ.pre.cum_x:
                    self.items_to_pack[self.cboxi].coord_x = self.smallestZ.pre.cum_x

                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.post.cum_z:
                        self.smallestZ.pre.cum_x = self.smallestZ.post.cum_x

                        if self.smallestZ.post.post is not None:
                            self.smallestZ.pre.post = self.smallestZ.post.post
                            self.smallestZ.post.post.pre = self.smallestZ.pre
                        else:
                            self.smallestZ.pre.post = None
                    else:
                        self.smallestZ.cum_z += self.cboxz
                elif self.smallestZ.pre.cum_x < self.px - self.smallestZ.cum_x:
                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.pre.cum_z:
                        self.smallestZ.cum_x -= self.cboxx
                        self.items_to_pack[self.cboxi].coord_x = self.smallestZ.cum_x
                    else:
                        self.items_to_pack[self.cboxi].coord_x = self.smallestZ.pre.cum_x
                        self.smallestZ.pre.post = ScrapPad()

                        self.smallestZ.pre.post.pre = self.smallestZ.pre
                        self.smallestZ.pre.post.post = self.smallestZ
                        self.smallestZ.pre = self.smallestZ.pre.post
                        self.smallestZ.pre.cum_x = self.smallestZ.pre.pre.cum_x + self.cboxx
                        self.smallestZ.pre.cum_z = self.smallestZ.cum_z + self.cboxz
                else:
                    if self.smallestZ.cum_z + self.cboxz == self.smallestZ.pre.cum_z:
                        self.smallestZ.pre.cum_x += self.cboxx
                        self.items_to_pack[self.cboxi].coord_x = self.smallestZ.pre.cum_x
                    else:
                        self.items_to_pack[self.cboxi].coord_x = self.smallestZ.cum_x - self.cboxx
                        self.smallestZ.post.pre = ScrapPad()

                        self.smallestZ.post.pre.post = self.smallestZ.post
                        self.smallestZ.post.pre.pre = self.smallestZ
                        self.smallestZ.post = self.smallestZ.post.pre
                        self.smallestZ.post.cum_x = self.smallestZ.cum_x
                        self.smallestZ.post.cum_z = self.smallestZ.cum_z + self.cboxz
                        self.smallestZ.cum_x -= self.cboxx

            else:
                # *** ALT DURUM-4B: YANLAR BİRBİRİNE EŞİT DEĞİL ***

                lenx = self.smallestZ.cum_x - self.smallestZ.pre.cum_x
                lenz = self.smallestZ.pre.cum_z - self.smallestZ.cum_z
                lpz = self.remainpz - self.smallestZ.cum_z
                self.find_box(lenx, self.layer_thickness, self.remainpy, lenz, lpz)
                self.check_found()

                if self.layerDone:
                    break
                if self.evened:
                    continue

                self.items_to_pack[self.cboxi].coord_y = self.packedy
                self.items_to_pack[self.cboxi].coord_z = self.smallestZ.cum_z
                self.items_to_pack[self.cboxi].coord_x = self.smallestZ.pre.cum_x

                if self.cboxx == (self.smallestZ.cum_x - self.smallestZ.pre.cum_x):
                    if (self.smallestZ.cum_z + self.cboxz) == self.smallestZ.pre.cum_z:
                        self.smallestZ.pre.cum_x = self.smallestZ.cum_x
                        self.smallestZ.pre.post = self.smallestZ.post
                        self.smallestZ.post.pre = self.smallestZ.pre
                    else:
                        self.smallestZ.cum_z += self.cboxz
                else:
                    if (self.smallestZ.cum_z + self.cboxz) == self.smallestZ.pre.cum_z:
                        self.smallestZ.pre.cum_x += self.cboxx
                    elif self.smallestZ.cum_z + self.cboxz == self.smallestZ.post.cum_z:
                        self.items_to_pack[self.cboxi].coord_x = self.smallestZ.cum_x - self.cboxx
                        self.smallestZ.cum_x -= self.cboxx
                    else:
                        self.smallestZ.pre.post = ScrapPad()

                        self.smallestZ.pre.post.pre = self.smallestZ.pre
                        self.smallestZ.pre.post.post = self.smallestZ
                        self.smallestZ.pre = self.smallestZ.pre.post
                        self.smallestZ.pre.cum_x = self.smallestZ.pre.pre.cum_x + self.cboxx
                        self.smallestZ.pre.cum_z = self.smallestZ.cum_z + self.cboxz

            self.volume_check()

    def report(self, container):
        self.quit = False

        if self.best_variant == 1:
            self.px, self.py, self.pz = container.length, container.height, container.width
        elif self.best_variant == 2:
            self.px, self.py, self.pz = container.width, container.height, container.length
        elif self.best_variant == 3:
            self.px, self.py, self.pz = container.width, container.length, container.height
        elif self.best_variant == 4:
            self.px, self.py, self.pz = container.height, container.length, container.width
        elif self.best_variant == 5:
            self.px, self.py, self.pz = container.length, container.width, container.height
        elif self.best_variant == 6:
            self.px, self.py, self.pz = container.height, container.width, container.length

        self.packing_best = True

        self.layers.clear()
        self.layers.append({'layer_eval': -1, 'layer_dim': 0})
        self.list_candit_layers()
        self.layers = sorted(self.layers, key=lambda l: l['layer_eval'])

        self.packed_volume = 0
        self.packedy = 0
        self.packing = True
        self.layer_thickness = self.layers[self.best_iteration]['layer_dim']
        self.remainpy = self.py
        self.remainpz = self.pz

        for x in range(1, len(self.items_to_pack)):
            self.items_to_pack[x].is_packed = False

        while self.packing and not self.quit:
            self.layerinlayer = 0
            self.layerDone = False
            self.pack_layer()
            self.packedy += self.layer_thickness
            self.remainpy = self.py - self.packedy

            if self.layerinlayer > 0.0001:
                prepackedy = self.packedy
                preremainpy = self.remainpy
                self.remainpy = self.layer_thickness - self.prelayer
                self.packedy = self.packedy - self.layer_thickness + self.prelayer
                self.remainpz = self.lilz
                self.layer_thickness = self.layerinlayer
                self.layerDone = False
                self.pack_layer()
                self.packedy = prepackedy
                self.remainpy = preremainpy
                self.remainpz = self.pz

            if not self.quit:
                self.find_layer(self.remainpy)

    def volume_check(self):

        self.items_to_pack[self.cboxi].is_packed = True
        self.items_to_pack[self.cboxi].pack_dim_x = self.cboxx
        self.items_to_pack[self.cboxi].pack_dim_y = self.cboxy
        self.items_to_pack[self.cboxi].pack_dim_z = self.cboxz
        self.packed_volume += self.items_to_pack[self.cboxi].volume
        self.packed_item_count += 1

        if self.packing_best:
            self.output_box_list()
        elif self.packed_volume == self.total_container_volume or self.packed_volume == self.total_item_volume:
            self.packing = False
            self.hundred_percent_packed = True


class Layer:

    def __init__(self, layer_dim, layer_eval):
        """
        :param layer_dim: Katman kalınlığı.
        :param layer_eval: Katman değerlendirme ağırlığı.
        """
        self.layer_dim = layer_dim
        self.layer_eval = layer_eval


class ScrapPad:
    """
    ScrapPad sınıfı, mevcut katmanın oluşturulma sürecinde kullanılan çift bağlı listeyi temsil eder.
    Her boşluğun sağ köşe koordinatlarını (x ve z) saklar.
    """

    def __init__(self, cum_x: float = 0.0, cum_z: float = 0.0):
        """
        :param cum_x: Boşluğun sağ köşesinin x koordinatı.
        :param cum_z: Boşluğun sağ köşesinin z koordinatı.
        """
        self.cum_x = cum_x
        self.cum_z = cum_z
        self.post: 'ScrapPad' = None  # Sonraki eleman (bağlı liste mantığında)
        self.pre: 'ScrapPad' = None  # Önceki eleman (bağlı liste mantığında)
