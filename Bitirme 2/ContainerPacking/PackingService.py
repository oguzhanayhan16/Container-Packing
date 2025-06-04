import time
import concurrent.futures
from typing import List
import copy
from .Packing.Algorithms.EB_AFIT import EB_AFIT
from .Packing.Algorithms.MCTS import MCTS
from .Packing.Porperties.ContainerPackingResult import ContainerPackingResult
from .Packing.Porperties.Container import Container
from .Packing.Porperties.Item import Item


class PackingService:

    @staticmethod
    def pack(containers: List['Container'], items_to_pack: List['Item'], algorithm_type_ids: List[int]):
        results = []

        def process_container(container):
            container_packing_result = ContainerPackingResult(container_id=container.id)

            def process_algorithm(algorithm_type_id):
                algorithm = PackingService.get_packing_algorithm_from_type_id(algorithm_type_id)
                print(algorithm)

                # Items listesi klonlanıyor
                items = [copy.deepcopy(item) for item in items_to_pack]

                start_time = time.time()
                algorithm_result = algorithm.run(container, items)

                elapsed_time = (time.time() - start_time) * 1000  # Milisaniyeye çevir
                algorithm_result.pack_time = elapsed_time
                # Container'ın hacmi ve item'ların yerleşme oranları hesaplanıyor
                try:
                    container_volume = container.length * container.width * container.height
                    packed_volume = sum(item.volume for item in algorithm_result.packed_items)
                    unpacked_volume = sum(item.volume for item in algorithm_result.unpacked_items)

                    # Sıfıra bölme hatasını önlemek için kontrol ekleyelim
                    if container_volume == 0:
                        raise ZeroDivisionError("Container volume is zero, cannot divide by zero.")

                    algorithm_result.percent_container_volume_packed = (packed_volume / container_volume) * 100

                    if (packed_volume + unpacked_volume) == 0:
                        raise ZeroDivisionError("Total item volume is zero, cannot calculate percentage.")

                    algorithm_result.percent_item_volume_packed = (packed_volume / (
                            packed_volume + unpacked_volume)) * 100

                except ZeroDivisionError as e:
                    print(f"ZeroDivisionError: {e}")
                    algorithm_result.percent_container_volume_packed = 0
                    algorithm_result.percent_item_volume_packed = 0

                # Sonuçları container packing result'a ekliyoruz

                try:
                    print(f"Algorithm Result for container {container.id}: {algorithm_result.algorithm_name}")
                    print(f"Packed items: {len(algorithm_result.packed_items)}")
                    print(f"Unpacked items: {len(algorithm_result.unpacked_items)}")

                    # Debug: Packing results listesini kontrol et

                    if container_packing_result.algorithm_packing_results is None:
                        raise AttributeError(
                            "container_packing_result.algorithm_packing_results is None, cannot append.")
                    container_packing_result.algorithm_packing_results.append(algorithm_result)
                    print("asd")
                except AttributeError as e:
                    print(
                        f"AttributeError: {e} - Check if 'container', 'algorithm_result', or 'container_packing_result' is initialized correctly.")
                except TypeError as e:
                    print(f"TypeError: {e} - Ensure that 'algorithm_packing_results' is a list and not None.")
                except Exception as e:
                    print(f"Unexpected error: {e}")

            # Paralel algoritma çalıştırma
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_algorithm, algorithm_type_ids)

            results.append(container_packing_result)

        # Konteynerleri paralel olarak işleme
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process_container, containers)

        return results

    @staticmethod
    def get_packing_algorithm_from_type_id(algorithm_type_id: int):
        if algorithm_type_id == 1:  # Örneğin, 1 numaralı algoritma EB-AFIT
            return EB_AFIT()  # EB-AFIT algoritmasını döndürüyoruz
        elif algorithm_type_id == 2:
            return MCTS()
        else:
            raise Exception("Invalid algorithm type.")
