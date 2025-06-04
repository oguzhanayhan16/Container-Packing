import unittest
import decimal  
from  ContainerPacking.Packing.Porperties.Item import Item
from ContainerPacking.PackingService import PackingService
from ContainerPacking.Packing.Porperties.Container import Container

from ContainerPacking.Packing.Algorithms.AlgorithmType import AlgorithmType


class ContainerPackingTests(unittest.TestCase):
    def test_EB_AFIT_Passes_700_Standard_Reference_Tests(self):
        resource_name = "ContainerPackingTests.DataFiles.ORLibrary.txt"
        
        with open(resource_name, "r") as reader:
            counter = 1
            
            while reader.readline() and counter <= 700:
                items_to_pack = []
                
                # First line in each test case is an ID. Skip it.
                # Second line states the results of the test, as reported in the EB-AFIT master's thesis, appendix E.
                test_results = reader.readline().strip().split(" ")
                
                # Third line defines the container dimensions.
                container_dims = reader.readline().strip().split(" ")
                
                # Fourth line states how many distinct item types we are packing.
                item_type_count = int(reader.readline().strip())
                
                for _ in range(item_type_count):
                    item_array = reader.readline().strip().split(" ")
                    item = Item(0, decimal.Decimal(item_array[1]), decimal.Decimal(item_array[3]), 
                                decimal.Decimal(item_array[5]), int(item_array[7]))
                    items_to_pack.append(item)
                
                containers = [Container(0, decimal.Decimal(container_dims[0]), 
                                       decimal.Decimal(container_dims[1]), 
                                       decimal.Decimal(container_dims[2]))]
                
                result = PackingService.pack(containers, items_to_pack, [AlgorithmType.EB_AFIT])
                algo_result = result[0].algorithm_packing_results[0]
                
                # Assert that the number of items we tried to pack equals the number stated in the published reference.
                self.assertEqual(len(algo_result.packed_items) + len(algo_result.unpacked_items), decimal.Decimal(test_results[1]))
                
                # Assert that the number of items successfully packed equals the number stated in the published reference.
                self.assertEqual(len(algo_result.packed_items), decimal.Decimal(test_results[2]))
                
                # Assert that the packed container volume percentage is equal to the published reference result.
                self.assertTrue(algo_result.percent_container_volume_packed == decimal.Decimal(test_results[3]) or
                                (algo_result.percent_container_volume_packed == decimal.Decimal("87.20") and
                                 decimal.Decimal(test_results[3]) == decimal.Decimal("87.21")))
                
                # Assert that the packed item volume percentage is equal to the published reference result.
                self.assertEqual(algo_result.percent_item_volume_packed, decimal.Decimal(test_results[4]))
                
                counter += 1
