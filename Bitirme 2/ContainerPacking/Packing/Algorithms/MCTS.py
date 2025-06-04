import copy
from ContainerPacking.Packing.Porperties.Container import Container
from ContainerPacking.Packing.Algorithms.ContainerMCTS import ContainerMCTS
from ContainerPacking.Packing.Porperties.Item import Item
from ContainerPacking.Packing.Porperties.PackingResult import AlgorithmPackingResult


class MCTS:

    def __init__(self, maxIterations=None, explorationConstant=0):
        print("MCTS algoritması çalıştırılıyor...")
        self.maxIterations = maxIterations
        self.explorationConstant = explorationConstant

    def run(self, container, items):
        SPACE_SCALING_FACTOR = 1

        try:
            expanded_items = []
            from collections import defaultdict
            total_quantity_map = defaultdict(int)
            # Her item türü için toplam miktarı topla
            for item in items:
                total_quantity_map[item.id] += item.quantity

            for item in items:
                for _ in range(item.quantity):
                    new_item = Item(item.id, item.dim1, item.dim2, item.dim3, item.name, quantity=1,
                                    total_quantity=total_quantity_map[item.id])  # Her kopya için quantity=1
                    expanded_items.append(new_item)

            # Konteyner nesnesini oluştur
            container_obj = Container(
                container_id="MCTS_CONTAINER",
                length=container.length,
                width=container.width,
                height=container.height,
                boxes=expanded_items,
                spaceOptimizationFactor=SPACE_SCALING_FACTOR,
                useDeepSearch=False
            )

            # MCTS başlat
            containerMCTS = ContainerMCTS(container=container_obj, maxIterations=self.maxIterations or 5000,
                                          explorationConstant=0.25)

            bestNode = containerMCTS.fill()
            if bestNode is None:
                raise Exception("En iyi düğüm bulunamadı. fill() fonksiyonu None döndürdü.")

            bestContainer = bestNode.projectedContainer
            nodeCBM = bestNode.totalCBM

            while bestNode is not None:
                bestContainer = bestNode.projectedContainer
                bestNode = containerMCTS.getBestLeaf(bestNode, explorationConstant=0)

            if bestContainer is None:
                raise Exception("Best container bulunamadı.")

            if bestContainer is not None:
                result_json = bestContainer.getResultsJSON()

            # Algoritma sonucu nesnesi
            result = AlgorithmPackingResult(
                algorithm_id=2,
                algorithm_name="MCTS",
                is_complete_pack=False,
                unpacked_items=[],
                packed_items=[]
            )

            # Kutuları sırayla yerleştir ve başarılı olanları ekle
            for item in expanded_items:
                success = container_obj.addBox(item)
                if success:
                    result.packed_items.append(item)
                else:
                    result.unpacked_items.append(item)

            if len(result.unpacked_items) == 0:
                result.is_complete_pack = True

            # Bilgilendirme çıktıları
            print("Eldeki Kutu Sayısı: %s @ %s m³" % (len(expanded_items), sum([i.volume for i in expanded_items])))

            print("Konteyner Boyutları: U:%s Y:%s G:%s @ %s m³" % (
                result_json["dimensions"]["length"], result_json["dimensions"]["height"],
                result_json["dimensions"]["width"], result_json["containerCBM"]
            ))
            print("Ölçeklenmiş Konteyner Boyutları: %s" % result_json["scaledDimensions"])
            print("----------------------------------")
            print("Düğüm Hacmi (CBM): %s" % nodeCBM)
            print("Tahmini Hacim: %s m³ | Kutu Sayısı: %s" % (result_json["cbm"], len(result_json["boxes"])))
            print("----------------------------------")

            return result

        except Exception as e:
            print(f"[MCTS] Bir hata oluştu: {e}")
            return None
